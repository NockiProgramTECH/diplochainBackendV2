"""
diplomas/views.py

MODIFICATION MetaMask :
- DiplomaIssueView      : supprimé sign_hash_ethereum() côté serveur.
                          Retourne maintenant le hash au frontend pour
                          que MetaMask le signe.
- Ajouté ConfirmEthSigView : reçoit la signature ETH de MetaMask,
                             la vérifie, et finalise le statut du diplôme.
- Toutes les vues de vérification : inchangées.
"""
from django.core.files.base import ContentFile

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from .models import Diploma
from .serializers import (
    DiplomaCreateSerializer,
    DiplomaDetailSerializer,
    DiplomaListSerializer,
    VerifyByFileSerializer,
    VerifyByHashSerializer,
    RevokeSerializer,
    ConfirmEthSigSerializer,
)
from .pdf_service import generate_diploma_pdf
from .blockchain_service import PolygonService
from universities.crypto_service import (
    hash_bytes,
    sign_diploma_hash,
    verify_diploma_signature,
    verify_eth_signature_from_metamask,
)


# ══════════════════════════════════════════════════════════════
# ÉMISSION — ÉTAPE 1/2
# Django génère le PDF, hash, signature RSA
# et retourne le hash au frontend pour MetaMask
# ══════════════════════════════════════════════════════════════

class DiplomaIssueView(APIView):
    """
    POST /api/diplomas/issue/

    Nouveau flux en 2 étapes :

    ÉTAPE 1 — Ce endpoint (Django fait tout sauf la signature ETH) :
      1. Crée le diplôme en base (status: draft)
      2. Génère le PDF
      3. Calcule hash SHA-256
      4. Signe avec la clé privée RSA (côté serveur)
      5. Sauvegarde (status: rsa_signed)
      6. Retourne le hash au frontend → MetaMask va le signer

    ÉTAPE 2 — POST /api/diplomas/<id>/confirm-eth-sig/
      Le frontend renvoie la signature ETH produite par MetaMask.
      Django la vérifie et passe le statut à "signed".
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Émettre un diplôme (Étape 1)",
        description="Génère le PDF, le signe (RSA), et retourne le hash à signer par MetaMask.",
        request=DiplomaCreateSerializer,
        responses={201: {"type": "object", "properties": {"message": {"type": "string"}, "diploma_id": {"type": "string"}, "hash_to_sign": {"type": "string"}}}}
    )
    def post(self, request):
        university = request.user

        if not university.is_verified:
            return Response(
                {"error": "Votre université n'est pas encore vérifiée par un administrateur."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not university.blockchain_address:
            return Response(
                {"error": "Aucun wallet MetaMask lié à ce compte. "
                          "Utilisez POST /api/auth/connect-wallet/"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = DiplomaCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        diploma = serializer.save()

        # ── Étape 1 : Générer le PDF ──────────────────────────
        try:
            pdf_bytes = generate_diploma_pdf({
                "student_first_name": diploma.student_first_name,
                "student_last_name":  diploma.student_last_name,
                "degree_title":       diploma.degree_title,
                "degree_level":       diploma.degree_level,
                "field_of_study":     diploma.field_of_study,
                "mention":            diploma.mention,
                "graduation_year":    diploma.graduation_year,
                "university_name":    university.name,
                "university_acronym": university.acronym,
                "university_city":    university.city,
                "university_country": university.country,
                "diploma_id":         str(diploma.id),
                "issued_at":          diploma.issued_at.strftime("%Y-%m-%d")
                                      if diploma.issued_at else "",
            })
            diploma.pdf_file.save(
                f"diploma_{diploma.id}.pdf",
                ContentFile(pdf_bytes),
                save=False,
            )
        except Exception as e:
            diploma.delete()
            return Response(
                {"error": f"Erreur génération PDF : {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # ── Étape 2 : Hash SHA-256 ────────────────────────────
        file_hash = hash_bytes(pdf_bytes)
        diploma.file_hash = file_hash

        # ── Étape 3 : Signature RSA (côté serveur) ────────────
        try:
            rsa_sig = sign_diploma_hash(file_hash, university.private_key_pem)
            diploma.rsa_signature = rsa_sig
        except Exception as e:
            diploma.delete()
            return Response(
                {"error": f"Erreur signature RSA : {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # ── Étape 4 : Sauvegarde partielle ───────────────────
        # status = "draft" jusqu'à confirmation de la signature ETH
        diploma.university_fingerprint_at_issue = university.crypto_fingerprint
        diploma.status = Diploma.STATUS_DRAFT
        diploma.save()

        # ── Étape 5 : Retourner le hash au frontend ───────────
        # React va passer ce hash à MetaMask pour signature
        return Response(
            {
                "message": (
                    "PDF généré et signé (RSA). "
                    "Faites signer le hash par MetaMask puis appelez "
                    "POST /api/diplomas/{id}/confirm-eth-sig/"
                ),
                "diploma_id":   str(diploma.id),
                "student":      diploma.student_full_name,
                "degree":       diploma.degree_title,
                # ← Ce hash doit être passé à MetaMask (personal_sign)
                "hash_to_sign": file_hash,
                "rsa_signature": rsa_sig,
                "pdf_url": (
                    request.build_absolute_uri(diploma.pdf_file.url)
                    if diploma.pdf_file else None
                ),
                "next_step": (
                    f"POST /api/diplomas/{diploma.id}/confirm-eth-sig/ "
                    "avec {eth_signature, signer_address}"
                ),
            },
            status=status.HTTP_201_CREATED,
        )


# ══════════════════════════════════════════════════════════════
# ÉMISSION — ÉTAPE 2/2  (NOUVEAU)
# Reçoit la signature MetaMask, la vérifie, finalise le diplôme
# ══════════════════════════════════════════════════════════════

class ConfirmEthSigView(APIView):
    """
    POST /api/diplomas/<id>/confirm-eth-sig/
    """
    permission_classes = [permissions.IsAuthenticated]


    @extend_schema(
        summary="Confirmer la signature MetaMask (Étape 2)",
        description="Reçoit la signature MetaMask et finalise l'émission du diplôme.",
        request=ConfirmEthSigSerializer,
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}, "status": {"type": "string"}}}}
    )
    def post(self, request, pk):
        university = request.user
        
        # Récupérer le diplôme
        try:
            # On cherche le diplôme par PK d'abord pour le debug
            diploma = Diploma.objects.get(id=pk)
            logger.info(f"Found Diploma: {diploma.id} | Hash: {diploma.file_hash} | Owner: {diploma.university.email}")
            
            # Vérification manuelle de propriété pour le debug
            if university and university.is_authenticated:
                if diploma.university != university:
                    logger.warning(f"Ownership mismatch: Diploma owner {diploma.university.id} != User {university.id}")
            
            if diploma.status != Diploma.STATUS_DRAFT:
                 logger.warning(f"Status mismatch: Current status is {diploma.status}")

        except Diploma.DoesNotExist:
            logger.warning(f"Diploma not found for PK={pk}")
            return Response(
                {"error": "Diplôme introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Valider le body
        serializer = ConfirmEthSigSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Serializer Errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        eth_signature   = serializer.validated_data["eth_signature"]
        signer_address  = serializer.validated_data["signer_address"]

        # Si on est en test (AllowAny), on utilise l'université du diplôme
        target_university = diploma.university

        # Vérification 1 : l'adresse qui signe = l'adresse du wallet enregistré
        if signer_address.lower() != target_university.blockchain_address.lower():
            logger.warning(f"Address mismatch: Signer {signer_address} != Wallet {target_university.blockchain_address}")
            return Response(
                {
                    "error": (
                        f"L'adresse signataire ({signer_address}) "
                        f"ne correspond pas au wallet enregistré "
                        f"({target_university.blockchain_address})."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Vérification 2 : la signature ETH est cryptographiquement valide
        valid, reason = verify_eth_signature_from_metamask(
            message=diploma.file_hash,
            eth_signature_hex=eth_signature,
            expected_address=target_university.blockchain_address,
        )

        if not valid:
            logger.error(f"Signature Validation Failed: {reason}")
            return Response(
                {
                    "error": f"Signature MetaMask invalide : {reason}",
                    "detail": (
                        "Assurez-vous que MetaMask a signé exactement le hash "
                        f"'{diploma.file_hash}' avec personal_sign."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Tout est valide — finaliser le diplôme
        diploma.eth_signature    = eth_signature
        diploma.eth_message_hash = diploma.file_hash
        diploma.status           = Diploma.STATUS_SIGNED
        diploma.save()

        return Response(
            {
                "message":      "Diplôme entièrement signé (RSA + MetaMask). Émission complète.",
                "diploma_id":   str(diploma.id),
                "student":      diploma.student_full_name,
                "status":       diploma.status,
                "file_hash":    diploma.file_hash,
                "rsa_signature": diploma.rsa_signature,
                "eth_signature": diploma.eth_signature,
                "signer_address": signer_address,
                "university_fingerprint": diploma.university_fingerprint_at_issue,
                "pdf_url": (
                    request.build_absolute_uri(diploma.pdf_file.url)
                    if diploma.pdf_file else None
                ),
            }
        )


# ══════════════════════════════════════════════════════════════
# ANCRAGE BLOCKCHAIN (NOUVEAU)
# ══════════════════════════════════════════════════════════════

class AnchorDiplomaView(APIView):
    """
    POST /api/diplomas/<id>/anchor/

    Ancre le hash du diplôme sur la blockchain Polygon.
    Utilise le portefeuille 'Gas Station' du serveur pour payer les frais.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Ancrer un diplôme sur la blockchain",
        description="Enregistre définitivement le hash du diplôme sur Polygon.",
        responses={200: {"type": "object", "properties": {"tx_hash": {"type": "string"}, "explorer_url": {"type": "string"}}}}
    )
    def post(self, request, pk):
        university = request.user

        try:
            diploma = Diploma.objects.get(
                id=pk,
                university=university,
                status=Diploma.STATUS_SIGNED
            )
        except Diploma.DoesNotExist:
            return Response(
                {"error": "Diplôme introuvable ou pas encore signé (ETH signature requise)."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if diploma.blockchain_tx_hash:
            return Response({"error": "Ce diplôme est déjà ancré sur la blockchain."})

        # Appel au service blockchain
        service = PolygonService()
        # On passe le hash, la signature MetaMask et l'adresse de l'université
        tx_hash, block_number = service.anchor_diploma(
            diploma.file_hash, 
            diploma.eth_signature, 
            university.blockchain_address
        )

        if tx_hash:
            diploma.blockchain_tx_hash = tx_hash
            diploma.blockchain_block_number = block_number
            diploma.status = Diploma.STATUS_ANCHORED
            diploma.save()

            return Response({
                "message": "Diplôme ancré avec succès sur Polygon Amoy.",
                "tx_hash": tx_hash,
                "block_number": block_number,
                "explorer_url": f"https://amoy.polygonscan.com/tx/{tx_hash}"
            })
        else:
            return Response(
                {"error": "Échec de l'ancrage blockchain. Vérifiez la configuration du serveur (RPC, Clé privée, Contrat)."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ══════════════════════════════════════════════════════════════
# VÉRIFICATION (inchangé)
# ══════════════════════════════════════════════════════════════

class VerifyByFileView(APIView):
    """POST /api/diplomas/verify/file/ — Vérification par upload PDF."""
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Vérifier par fichier PDF",
        description="Uploadez un PDF pour vérifier son authenticité.",
        request=VerifyByFileSerializer,
        responses={200: {"type": "object", "properties": {"valid": {"type": "boolean"}, "message": {"type": "string"}}}}
    )
    def post(self, request):
        serializer = VerifyByFileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["pdf_file"]
        diploma_id    = serializer.validated_data.get("diploma_id")
        file_bytes    = uploaded_file.read()
        computed_hash = hash_bytes(file_bytes)

        try:
            diploma = (
                Diploma.objects.get(id=diploma_id, is_revoked=False)
                if diploma_id
                else Diploma.objects.get(file_hash=computed_hash, is_revoked=False)
            )
        except Diploma.DoesNotExist:
            return Response(
                {"valid": False, "reason": "not_found", "computed_hash": computed_hash},
                status=status.HTTP_404_NOT_FOUND,
            )

        if computed_hash != diploma.file_hash:
            return Response({
                "valid": False, "reason": "hash_mismatch",
                "computed_hash": computed_hash, "stored_hash": diploma.file_hash,
            })

        valid, reason = verify_diploma_signature(
            diploma.file_hash, diploma.rsa_signature,
            diploma.university.public_key_pem,
        )
        if not valid:
            return Response({"valid": False, "reason": reason})

        fingerprint_match = (
            diploma.university_fingerprint_at_issue
            == diploma.university.crypto_fingerprint
        )

        # Vérification 3 : Blockchain (optionnel si configuré)
        service = PolygonService()
        blockchain_verified = False
        if diploma.blockchain_tx_hash:
            # On vérifie si le hash est réellement dans le contrat
            blockchain_verified = service.verify_on_chain(diploma.file_hash)

        return Response({
            "valid": True, "reason": "authentic",
            "message": "Diplôme AUTHENTIQUE.",
            "diploma": {
                "id": str(diploma.id), "student": diploma.student_full_name,
                "degree": diploma.degree_title, "field": diploma.field_of_study,
                "mention": diploma.mention, "year": diploma.graduation_year,
                "issued_at": diploma.issued_at.isoformat(),
            },
            "university": {
                "name": diploma.university.name,
                "acronym": diploma.university.acronym,
                "blockchain_address": diploma.university.blockchain_address,
                "is_verified": diploma.university.is_verified,
            },
            "crypto": {
                "hash_match": True, "rsa_signature_valid": True,
                "fingerprint_match": fingerprint_match,
                "eth_signature_present": bool(diploma.eth_signature),
                "blockchain_anchored": diploma.is_blockchain_anchored,
                "blockchain_verified_realtime": blockchain_verified,
            },
        })


class VerifyByHashView(APIView):
    """POST /api/diplomas/verify/hash/ — Vérification par hash."""
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Vérifier par hash",
        description="Vérifiez l'authenticité d'un diplôme via son hash SHA-256.",
        request=VerifyByHashSerializer,
        responses={200: {"type": "object", "properties": {"valid": {"type": "boolean"}, "diploma_id": {"type": "string"}}}}
    )
    def post(self, request):
        serializer = VerifyByHashSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file_hash = serializer.validated_data["file_hash"]

        try:
            diploma = Diploma.objects.get(file_hash=file_hash, is_revoked=False)
        except Diploma.DoesNotExist:
            return Response(
                {"valid": False, "reason": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        valid, reason = verify_diploma_signature(
            diploma.file_hash, diploma.rsa_signature,
            diploma.university.public_key_pem,
        )
        return Response({
            "valid": valid, "reason": reason,
            "diploma_id": str(diploma.id),
            "student": diploma.student_full_name,
            "university": diploma.university.name,
            "degree": diploma.degree_title,
            "issued_at": diploma.issued_at.isoformat(),
            "blockchain_anchored": diploma.is_blockchain_anchored,
        })


# ══════════════════════════════════════════════════════════════
# LISTE, DÉTAIL, RÉVOCATION (inchangés)
# ══════════════════════════════════════════════════════════════

class MyDiplomasView(generics.ListAPIView):
    serializer_class   = DiplomaListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Diploma.objects.filter(university=self.request.user)


class DiplomaDetailView(generics.RetrieveAPIView):
    queryset           = Diploma.objects.all()
    serializer_class   = DiplomaDetailSerializer
    permission_classes = [permissions.AllowAny]


class RevokeDiplomaView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Révoquer un diplôme",
        description="Invalide un diplôme pour une raison donnée.",
        request=RevokeSerializer,
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}}
    )
    def post(self, request, pk):
        try:
            diploma = Diploma.objects.get(id=pk, university=request.user)
        except Diploma.DoesNotExist:
            return Response(
                {"error": "Diplôme introuvable ou non autorisé."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if diploma.is_revoked:
            return Response({"error": "Ce diplôme est déjà révoqué."})

        serializer = RevokeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        diploma.is_revoked        = True
        diploma.status            = Diploma.STATUS_REVOKED
        diploma.revocation_reason = serializer.validated_data["reason"]
        diploma.save()

        return Response({
            "message":    "Diplôme révoqué avec succès.",
            "diploma_id": str(diploma.id),
            "reason":     diploma.revocation_reason,
        })

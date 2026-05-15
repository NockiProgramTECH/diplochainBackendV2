"""
universities/views.py

MODIFICATION MetaMask :
- RegisterUniversityView    : inchangée en logique, juste la réponse mise à jour
- Ajouté ConnectWalletView  : génère un challenge, puis accepte la signature MetaMask
- Ajouté WalletChallengeView: génère le message à signer par MetaMask
- MyKeysView                : supprimé blockchain_private_key de la réponse
"""
import random
import uuid
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from .models import University
from .serializers import (
    UniversityRegisterSerializer,
    UniversityPublicSerializer,
    UniversityProfileSerializer,
    UniversityKeysSerializer,
    ConnectWalletSerializer,
)
from .crypto_service import generate_rsa_keypair_only


# ══════════════════════════════════════════════════════════════
# INSCRIPTION
# ══════════════════════════════════════════════════════════════

class RegisterUniversityView(generics.CreateAPIView):
    """
    POST /api/auth/register/

    Body attendu (React envoie l'adresse MetaMask déjà connectée) :
    {
        "email"              : "admin@uo.bf",
        "name"               : "Université de Ouagadougou",
        "acronym"            : "UO",
        "country"            : "Burkina Faso",
        "city"               : "Ouagadougou",
        "blockchain_address" : "0x527c545...",   ← depuis MetaMask
        "password"           : "...",
        "password_confirm"   : "..."
    }
    """
    queryset             = University.objects.all()
    serializer_class     = UniversityRegisterSerializer
    permission_classes   = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        university = serializer.save()

        return Response(
            {
                "message":            "Université enregistrée avec succès.",
                "university_id":      str(university.id),
                "name":               university.name,
                # Adresse MetaMask confirmée
                "blockchain_address": university.blockchain_address,
                # Empreinte : SHA256(adresse_metamask + pubkey_rsa)
                "crypto_fingerprint": university.crypto_fingerprint,
                # Clé publique RSA — peut être partagée
                "public_key_pem":     university.public_key_pem,
                "next_steps": (
                    "Attendez la validation de votre compte par un administrateur. "
                    "Votre clé privée RSA est sécurisée côté serveur. "
                    "Votre clé privée Ethereum reste dans MetaMask."
                ),
            },
            status=status.HTTP_201_CREATED,
        )


# ══════════════════════════════════════════════════════════════
# CHALLENGE METAMASK — NOUVEAU
# Flux en 2 étapes pour lier/changer un wallet de façon sécurisée
# ══════════════════════════════════════════════════════════════

class WalletChallengeView(APIView):
    """
    GET /api/auth/wallet-challenge/

    Génère un message unique à faire signer par MetaMask.
    Le frontend React reçoit ce message, le passe à MetaMask
    (personal_sign), puis soumet la signature à ConnectWalletView.

    Pourquoi un challenge ? Pour prouver que l'université contrôle
    vraiment l'adresse MetaMask qu'elle déclare, sans exposer
    la clé privée.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Générer un challenge MetaMask",
        description="Génère un message unique que l'université doit signer avec MetaMask pour prouver la possession du wallet.",
        responses={200: {"type": "object", "properties": {"challenge": {"type": "string"}, "instruction": {"type": "string"}}}}
    )
    def get(self, request):
        # Message unique horodaté — change à chaque appel
        # Le frontend doit signer EXACTEMENT ce message avec MetaMask
        challenge = f"DiploChain:connect-wallet:{uuid.uuid4()}:{int(timezone.now().timestamp())}"

        # Stocker temporairement dans la session avec timestamp pour expiration
        request.session["wallet_challenge"] = challenge
        request.session["wallet_challenge_ts"] = timezone.now().timestamp()
        request.session.save()

        return Response(
            {
                "challenge": challenge,
                "instruction": (
                    "Passez ce message à MetaMask via personal_sign. "
                    "Soumettez ensuite l'adresse et la signature à "
                    "POST /api/auth/connect-wallet/"
                ),
            }
        )


class ConnectWalletView(APIView):
    """
    POST /api/auth/connect-wallet/

    Permet à une université authentifiée de lier ou changer
    son adresse MetaMask.

    Body attendu :
    {
        "blockchain_address" : "0x...",
        "signed_message"     : "0x...",   ← signature de MetaMask
        "challenge_message"  : "DiploChain:connect-wallet:uuid:timestamp"
    }

    Vérifie que MetaMask a bien signé le challenge,
    puis enregistre la nouvelle adresse et recalcule l'empreinte.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Lier un wallet MetaMask",
        description="Vérifie la signature du challenge et lie l'adresse MetaMask au compte de l'université.",
        request=ConnectWalletSerializer,
        responses={
            200: {"type": "object", "properties": {"message": {"type": "string"}, "blockchain_address": {"type": "string"}, "crypto_fingerprint": {"type": "string"}, "warning": {"type": "string"}}},
            409: {"type": "object", "properties": {"error": {"type": "string"}}}
        }
    )
    def post(self, request):
        # Vérification de l'expiration du challenge (ex: 5 minutes)
        challenge_ts = request.session.get("wallet_challenge_ts")
        if not challenge_ts or (timezone.now().timestamp() - challenge_ts) > 300:
            return Response(
                {"error": "Le challenge a expiré. Veuillez en générer un nouveau via GET /api/auth/wallet-challenge/"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        serializer = ConnectWalletSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        university = request.user
        new_address = serializer.validated_data["blockchain_address"]

        # Unicité : adresse pas déjà prise par une autre université
        conflict = University.objects.filter(
            blockchain_address__iexact=new_address
        ).exclude(pk=university.pk).first()

        if conflict:
            return Response(
                {"error": "Cette adresse MetaMask est déjà utilisée par une autre université."},
                status=status.HTTP_409_CONFLICT,
            )

        # Mise à jour de l'adresse et recalcul de l'empreinte
        university.blockchain_address = new_address
        university.wallet_connected_at = timezone.now()
        # Le save() recalcule automatiquement crypto_fingerprint
        university.save()

        return Response(
            {
                "message":            "Wallet MetaMask lié avec succès.",
                "blockchain_address": university.blockchain_address,
                "crypto_fingerprint": university.crypto_fingerprint,
                "warning": (
                    "L'empreinte cryptographique a changé. "
                    "Les diplômes émis avant ce changement restent vérifiables "
                    "avec l'ancienne empreinte stockée au moment de leur émission."
                ),
            }
        )

class PasswordResetRequestView(APIView):
    """POST /api/auth/password-reset/request/"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from .serializers import PasswordResetRequestSerializer
        from .models import University, PasswordResetCode

        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        university = University.objects.filter(email__iexact=email).first()
        if university:
            # Invalider les anciens codes encore actifs
            PasswordResetCode.objects.filter(
                university=university,
                used=False,
                expires_at__gt=timezone.now(),
            ).update(used=True)

            code = "".join(random.choices("0123456789", k=6))
            expires_at = timezone.now() + timedelta(minutes=30)
            PasswordResetCode.objects.create(
                university=university,
                code=code,
                expires_at=expires_at,
            )

            subject = "Réinitialisation du mot de passe DiploChain"
            message = (
                f"Bonjour {university.name},\n\n"
                f"Voici votre code de réinitialisation de mot de passe : {code}\n"
                "Ce code est valable 30 minutes.\n\n"
                "Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.\n\n"
                "Cordialement,\n"
                "L'équipe DiploChain"
            )
            send_mail(
                subject,
                message,
                getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@diplochain.local"),
                [university.email],
                fail_silently=True,
            )

        return Response(
            {
                "message": (
                    "Si cet e-mail est enregistré, un code de réinitialisation a été envoyé. "
                    "Vérifiez votre boîte de réception."
                )
            }
        )


class PasswordResetConfirmView(APIView):
    """POST /api/auth/password-reset/confirm/"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from .serializers import PasswordResetConfirmSerializer
        from .models import University, PasswordResetCode

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]
        password = serializer.validated_data["password"]

        university = University.objects.filter(email__iexact=email).first()
        if not university:
            return Response(
                {"detail": "Adresse e-mail ou code invalide."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reset_code = PasswordResetCode.objects.filter(
            university=university,
            code=code,
            used=False,
            expires_at__gte=timezone.now(),
        ).order_by("-created_at").first()

        if not reset_code:
            return Response(
                {"detail": "Adresse e-mail ou code invalide."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        university.set_password(password)
        university.save()
        reset_code.used = True
        reset_code.save()

        return Response(
            {"message": "Le mot de passe a été réinitialisé avec succès."}
        )

# ══════════════════════════════════════════════════════════════
# PROFIL & CLÉS
# ══════════════════════════════════════════════════════════════

class MyProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /api/auth/profile/   — Profil de l'université connectée
    PUT /api/auth/profile/   — Mise à jour du profil (nom, ville, logo...)
    """
    serializer_class   = UniversityProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class MyKeysView(APIView):
    """
    GET /api/auth/keys/

    Retourne les clés RSA de l'université.
    SUPPRIMÉ : blockchain_private_key — elle est dans MetaMask.

    NOTE : en production, restreindre cet endpoint à une IP de confiance
    ou exiger une confirmation 2FA avant de retourner la clé privée RSA.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Récupérer les clés RSA",
        description="Retourne les clés publique et privée RSA de l'université. La clé privée est confidentielle.",
        responses={200: UniversityKeysSerializer}
    )
    def get(self, request):
        serializer = UniversityKeysSerializer(request.user)
        data = serializer.data
        # SÉCURITÉ : On ne renvoie plus la clé privée RSA par défaut via l'API.
        # En production, cela doit passer par une procédure sécurisée.
        data.pop("private_key_pem", None) 
        
        return Response(
            {
                "warning": (
                    "Pour des raisons de sécurité, la clé privée RSA n'est plus exposée via cet endpoint. "
                    "Elle reste stockée de manière sécurisée sur le serveur."
                ),
                "keys": data,
            }
        )


# ══════════════════════════════════════════════════════════════
# LISTES PUBLIQUES
# ══════════════════════════════════════════════════════════════

class UniversityPublicDetailView(generics.RetrieveAPIView):
    """GET /api/universities/<id>/ — Profil public d'une université."""
    queryset           = University.objects.filter(is_active=True)
    serializer_class   = UniversityPublicSerializer
    permission_classes = [permissions.AllowAny]


class UniversityListView(generics.ListAPIView):
    """GET /api/universities/ — Liste des universités vérifiées."""
    queryset           = University.objects.filter(is_active=True, is_verified=True)
    serializer_class   = UniversityPublicSerializer
    permission_classes = [permissions.AllowAny]

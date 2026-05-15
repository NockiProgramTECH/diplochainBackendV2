"""
universities/serializers.py

MODIFICATION MetaMask :
- UniversityRegisterSerializer : reçoit maintenant blockchain_address depuis le frontend
  (MetaMask). Ne génère plus de clés ETH. Génère uniquement les clés RSA.
- Ajouté    : ConnectWalletSerializer — pour lier/changer le wallet MetaMask après inscription
- Conservé  : UniversityPublicSerializer, UniversityProfileSerializer
- Modifié   : UniversityKeysSerializer — supprimé blockchain_private_key
"""
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import University
from .crypto_service import (
    generate_rsa_keypair_only,
    is_valid_eth_address,
    encrypt_private_key,
)


# ══════════════════════════════════════════════════════════════
# 1. INSCRIPTION — NOUVEAU
#    L'université fournit son adresse MetaMask dans le body.
#    Django génère uniquement les clés RSA.
# ══════════════════════════════════════════════════════════════

class UniversityRegisterSerializer(serializers.ModelSerializer):
    """
    POST /api/auth/register/

    Nouveau champ requis : blockchain_address
      → fourni par React après que l'utilisateur a connecté MetaMask
      → format attendu : "0x" + 40 caractères hexadécimaux

    Django NE génère plus de clé ETH.
    Django génère UNIQUEMENT la paire RSA-2048.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )
    # Adresse MetaMask — fournie par le frontend, pas générée par Django
    blockchain_address = serializers.CharField(
        required=True,
        max_length=42,
        help_text="Adresse Ethereum de votre wallet MetaMask (0x...)",
    )

    class Meta:
        model = University
        fields = [
            "id", "email", "name", "acronym",
            "country", "city", "website",
            "blockchain_address",          # ← NOUVEAU : vient de MetaMask
            "password", "password_confirm",
        ]
        read_only_fields = ["id"]

    # ── Validations ─────────────────────────────────────────

    def validate_blockchain_address(self, value: str) -> str:
        """
        Vérifie que l'adresse Ethereum est valide (format 0x + 40 hex).
        Vérifie qu'elle n'est pas déjà utilisée par une autre université.
        """
        if not is_valid_eth_address(value):
            raise serializers.ValidationError(
                "Adresse Ethereum invalide. "
                "Format attendu : 0x suivi de 40 caractères hexadécimaux."
            )
        # Unicité : une adresse MetaMask = une seule université
        if University.objects.filter(
            blockchain_address__iexact=value
        ).exists():
            raise serializers.ValidationError(
                "Cette adresse MetaMask est déjà associée à une université."
            )
        # Normaliser en checksum (minuscules pour la cohérence)
        return value.lower()

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password": "Les mots de passe ne correspondent pas."}
            )
        return attrs

    # ── Création ────────────────────────────────────────────

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        blockchain_address = validated_data["blockchain_address"]

        # Django génère UNIQUEMENT les clés RSA
        # L'adresse MetaMask est passée pour calculer l'empreinte
        try:
            rsa_keys = generate_rsa_keypair_only(
                blockchain_address=blockchain_address
            )
        except Exception as e:
            raise serializers.ValidationError(
                {"crypto": f"Erreur de génération des clés RSA : {str(e)}"}
            )

        university = University(
            **validated_data,
            # Clés RSA (générées par Django) — Chiffrée au repos
            private_key_pem=encrypt_private_key(rsa_keys["private_key_pem"]),
            public_key_pem=rsa_keys["public_key_pem"],
            # Empreinte : SHA256(adresse_metamask + pubkey_rsa)
            crypto_fingerprint=rsa_keys["crypto_fingerprint"],
            # Date de liaison MetaMask
            wallet_connected_at=timezone.now(),
        )
        university.set_password(password)
        university.save()
        return university


# ══════════════════════════════════════════════════════════════
# 2. LIER / CHANGER LE WALLET METAMASK — NOUVEAU
#    Permet à une université de changer son adresse MetaMask.
#    Recalcule l'empreinte cryptographique.
#    ATTENTION : cela invalide les anciennes vérifications d'empreinte.
# ══════════════════════════════════════════════════════════════

class ConnectWalletSerializer(serializers.Serializer):
    """
    POST /api/auth/connect-wallet/

    Body attendu du frontend React :
    {
        "blockchain_address" : "0x...",       ← nouvelle adresse MetaMask
        "signed_message"     : "0x...",       ← MetaMask a signé un message de preuve
        "challenge_message"  : "DiploChain:connect:uuid-..." ← le message signé
    }

    Le backend vérifie que le frontend contrôle vraiment cette adresse
    en vérifiant la signature MetaMask avant de l'enregistrer.
    """
    blockchain_address = serializers.CharField(max_length=42)
    signed_message     = serializers.CharField(
        help_text="Signature hex produite par MetaMask (personal_sign)"
    )
    challenge_message  = serializers.CharField(
        help_text="Le message exact qui a été signé par MetaMask"
    )

    def validate_blockchain_address(self, value: str) -> str:
        if not is_valid_eth_address(value):
            raise serializers.ValidationError("Adresse Ethereum invalide.")
        return value.lower()

    def validate(self, attrs):
        """
        Vérifie que la signature MetaMask est valide :
        l'adresse fournie a bien signé le challenge_message.
        """
        from .crypto_service import verify_eth_signature_from_metamask
        valid, reason = verify_eth_signature_from_metamask(
            message=attrs["challenge_message"],
            eth_signature_hex=attrs["signed_message"],
            expected_address=attrs["blockchain_address"],
        )
        if not valid:
            raise serializers.ValidationError(
                {
                    "signed_message": (
                        f"Signature MetaMask invalide ({reason}). "
                        "Impossible de vérifier que vous contrôlez cette adresse."
                    )
                }
            )
        return attrs

class PasswordResetRequestSerializer(serializers.Serializer):
    """Demande de code de réinitialisation de mot de passe."""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Confirmation de la réinitialisation de mot de passe avec code."""

    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password": "Les mots de passe ne correspondent pas."}
            )
        return attrs

# ══════════════════════════════════════════════════════════════
# 3. PROFIL PUBLIC — légèrement modifié
#    Supprimé : blockchain_public_key (on ne la stocke plus)
# ══════════════════════════════════════════════════════════════

class UniversityPublicSerializer(serializers.ModelSerializer):
    """
    Profil public d'une université.
    Utilisé pour la vérification des diplômes par les tiers.
    """
    diplomas_count = serializers.SerializerMethodField()

    class Meta:
        model = University
        fields = [
            "id", "name", "acronym", "country", "city", "website",
            "blockchain_address",   # adresse MetaMask publique
            "public_key_pem",       # clé publique RSA (vérification signatures)
            "crypto_fingerprint",
            "is_verified",
            "date_joined",
            "wallet_connected_at",
            "diplomas_count",
        ]

    def get_diplomas_count(self, obj):
        return obj.diploma_set.filter(is_revoked=False).count()


# ══════════════════════════════════════════════════════════════
# 4. PROFIL CONNECTÉ — modifié
# ══════════════════════════════════════════════════════════════

class UniversityProfileSerializer(serializers.ModelSerializer):
    """
    Profil complet de l'université connectée.
    Jamais la clé privée RSA dans cette vue.
    """
    class Meta:
        model = University
        fields = [
            "id", "email", "name", "acronym", "country", "city",
            "website", "logo",
            "blockchain_address",
            "public_key_pem",
            "crypto_fingerprint",
            "is_verified",
            "date_joined",
            "wallet_connected_at",
        ]
        read_only_fields = [
            "id",
            "blockchain_address",
            "public_key_pem",
            "crypto_fingerprint",
            "date_joined",
            "wallet_connected_at",
        ]


# ══════════════════════════════════════════════════════════════
# 5. EXPORT CLÉS — modifié (suppression clé ETH privée)
# ══════════════════════════════════════════════════════════════

class UniversityKeysSerializer(serializers.ModelSerializer):
    """
    Export des clés RSA de l'université.
    SUPPRIMÉ : blockchain_private_key — elle est dans MetaMask, pas ici.
    """
    class Meta:
        model = University
        fields = [
            "id", "name",
            "blockchain_address",   # adresse publique MetaMask
            "public_key_pem",       # clé publique RSA
            "private_key_pem",      # clé privée RSA (sensible — endpoint protégé)
            "crypto_fingerprint",
        ]

"""
diplomas/serializers.py

MODIFICATION MetaMask :
- Ajouté ConfirmEthSigSerializer — valide la signature ETH de MetaMask
- Reste inchangé
"""
from rest_framework import serializers
from .models import Diploma
from universities.serializers import UniversityPublicSerializer


class DiplomaCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diploma
        fields = [
            "student_first_name", "student_last_name", "student_dob",
            "student_national_id", "degree_title", "degree_level",
            "field_of_study", "mention", "graduation_year",
        ]

    def create(self, validated_data):
        university = self.context["request"].user
        return Diploma.objects.create(university=university, **validated_data)


# ══════════════════════════════════════════════════════════════
# NOUVEAU — Validation de la signature MetaMask
# ══════════════════════════════════════════════════════════════

class ConfirmEthSigSerializer(serializers.Serializer):
    """
    Body attendu pour POST /api/diplomas/<id>/confirm-eth-sig/
    """
    eth_signature = serializers.CharField(required=True)
    signer_address = serializers.CharField(required=True)

    def validate_eth_signature(self, value: str) -> str:
        # On nettoie juste le préfixe si besoin, mais on laisse passer la longueur
        return value if value.startswith("0x") else "0x" + value

    def validate_signer_address(self, value: str) -> str:
        # On laisse passer l'adresse telle quelle, la vue s'en chargera
        return value.strip()


# ══════════════════════════════════════════════════════════════
# Sérialiseurs existants — inchangés
# ══════════════════════════════════════════════════════════════

class DiplomaDetailSerializer(serializers.ModelSerializer):
    university             = UniversityPublicSerializer(read_only=True)
    student_full_name      = serializers.CharField(read_only=True)
    is_blockchain_anchored = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Diploma
        fields = [
            "id", "university",
            "student_full_name", "student_first_name", "student_last_name",
            "student_dob", "student_national_id",
            "degree_title", "degree_level", "field_of_study", "mention",
            "graduation_year",
            "file_hash", "rsa_signature", "university_fingerprint_at_issue",
            "eth_signature", "eth_message_hash",
            "blockchain_tx_hash", "blockchain_block_number",
            "status", "is_revoked", "revocation_reason",
            "is_blockchain_anchored", "issued_at", "updated_at",
        ]
        read_only_fields = fields


class DiplomaListSerializer(serializers.ModelSerializer):
    university_name   = serializers.CharField(source="university.name", read_only=True)
    student_full_name = serializers.CharField(read_only=True)

    class Meta:
        model  = Diploma
        fields = [
            "id", "university_name", "student_full_name",
            "degree_title", "degree_level", "field_of_study",
            "graduation_year", "status", "is_revoked",
            "file_hash", "issued_at",
        ]


class VerifyByFileSerializer(serializers.Serializer):
    pdf_file   = serializers.FileField(required=True)
    diploma_id = serializers.UUIDField(required=False)


class VerifyByHashSerializer(serializers.Serializer):
    file_hash = serializers.CharField(min_length=64, max_length=64)


class RevokeSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, required=True)

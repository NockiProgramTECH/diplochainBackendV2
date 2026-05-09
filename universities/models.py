"""
universities/models.py

MODIFICATION MetaMask :
- Supprimé : blockchain_private_key  (la clé ETH privée ne doit JAMAIS être stockée côté serveur)
- Supprimé : blockchain_public_key   (non nécessaire, l'adresse suffit pour l'empreinte)
- Ajouté   : blockchain_address fournie par le frontend (MetaMask)
- Modifié  : compute_crypto_fingerprint() — lie adresse ETH + clé publique RSA uniquement
- Ajouté   : wallet_connected_at — date de liaison MetaMask
"""
import uuid
import hashlib

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UniversityManager(BaseUserManager):
    def create_user(self, email, name, country, password=None, **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, country=country, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, country="BF", password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, name, country, password, **extra_fields)


class University(AbstractBaseUser, PermissionsMixin):
    """
    Utilisateur = Université / École.

    Architecture des clés avec MetaMask :
    ─────────────────────────────────────
    • Clé privée ETH   → dans MetaMask (jamais sur notre serveur ✓)
    • Adresse ETH      → fournie par MetaMask à l'inscription, stockée ici
    • Clé privée RSA   → générée et stockée côté serveur (signe les PDF)
    • Clé publique RSA → dérivée de la clé privée RSA, stockée ici

    Empreinte cryptographique :
      SHA256(blockchain_address + rsa_public_key_pem)
      → lie l'identité MetaMask à la capacité de signer des diplômes
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ── Informations institution ─────────────────────────────────
    email    = models.EmailField(unique=True)
    name     = models.CharField(max_length=255, verbose_name="Nom de l'université")
    acronym  = models.CharField(max_length=20,  verbose_name="Sigle (ex: UO, 2iE)")
    country  = models.CharField(max_length=100, default="Burkina Faso")
    city     = models.CharField(max_length=100, default="Ouagadougou")
    website  = models.URLField(blank=True, null=True)
    logo     = models.ImageField(upload_to="university_logos/", blank=True, null=True)

    # ── Clés RSA (gérées par Django) ────────────────────────────
    # Clé privée RSA — signe les hash SHA-256 des PDF
    # En production : stocker dans un KMS, pas en clair en DB
    private_key_pem = models.TextField(
        verbose_name="Clé privée RSA (PEM)",
        blank=True,
    )
    # Clé publique RSA — dérivée de la clé privée, publique
    public_key_pem = models.TextField(
        verbose_name="Clé publique RSA (PEM)",
        blank=True,
    )

    # ── Wallet MetaMask (géré par le frontend) ──────────────────
    # L'université connecte son wallet MetaMask à l'inscription.
    # Django ne connaît QUE l'adresse publique — jamais la clé privée.
    blockchain_address = models.CharField(
        max_length=42,
        unique=True,
        blank=True,
        verbose_name="Adresse Ethereum MetaMask (0x...)",
        help_text="Fournie par MetaMask côté frontend à l'inscription.",
    )
    wallet_connected_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Date de liaison MetaMask",
    )

    # ── Empreinte cryptographique ────────────────────────────────
    # SHA256(blockchain_address + public_key_pem)
    # Lie l'adresse MetaMask à la clé publique RSA.
    # Si l'un des deux change, l'empreinte change → tous les diplômes
    # émis avec l'ancienne empreinte restent vérifiables.
    crypto_fingerprint = models.CharField(
        max_length=64,
        blank=True,
        verbose_name="Empreinte cryptographique SHA256",
    )

    # ── Auth Django ──────────────────────────────────────────────
    is_active    = models.BooleanField(default=True)
    is_staff     = models.BooleanField(default=False)
    is_verified  = models.BooleanField(
        default=False,
        verbose_name="Université vérifiée par l'admin",
    )
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UniversityManager()

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["name", "country"]

    class Meta:
        verbose_name         = "Université"
        verbose_name_plural  = "Universités"

    def __str__(self):
        return f"{self.name} ({self.acronym})"

    def compute_crypto_fingerprint(self) -> str:
        """
        Calcule l'empreinte qui lie :
          - L'adresse Ethereum (identité MetaMask)
          - La clé publique RSA (capacité de signature)

        SHA256(adresse_eth_lowercase + rsa_public_key_pem)

        Note : on n'inclut plus blockchain_public_key (secp256k1)
        car on ne la stocke plus — l'adresse seule suffit à identifier
        le wallet de façon unique.
        """
        raw = (
            self.blockchain_address.lower()
            + self.public_key_pem.strip()
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def save(self, *args, **kwargs):
        # Normalisation de l'adresse Ethereum en Checksum Address
        if self.blockchain_address:
            from web3 import Web3
            self.blockchain_address = Web3().to_checksum_address(self.blockchain_address)

        # Recalcule l'empreinte si les deux éléments sont présents
        if self.blockchain_address and self.public_key_pem:
            self.crypto_fingerprint = self.compute_crypto_fingerprint()
        super().save(*args, **kwargs)

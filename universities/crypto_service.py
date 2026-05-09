"""
universities/crypto_service.py

MODIFICATION MetaMask :
- Supprimé : generate_ethereum_keypair()     → MetaMask s'en charge
- Supprimé : generate_university_keypairs()  → remplacé par generate_rsa_keypair_only()
- Supprimé : sign_hash_ethereum()            → MetaMask s'en charge
- Conservé : generate_rsa_keypair_only()     → Django génère uniquement le RSA
- Conservé : hash_bytes(), hash_file()       → inchangés
- Conservé : sign_diploma_hash()             → Django signe toujours avec RSA
- Conservé : verify_diploma_signature()      → vérification RSA inchangée
- Ajouté   : verify_eth_signature_from_metamask() → vérifie la sig MetaMask reçue du frontend
"""

import hashlib
import base64
from typing import Tuple, Dict

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
from cryptography.fernet import Fernet
from django.conf import settings


# ══════════════════════════════════════════════════════════════
# 1. GÉNÉRATION CLÉ RSA-2048 (côté serveur — inchangé)
#    Django génère uniquement les clés RSA.
#    Les clés Ethereum sont dans MetaMask.
# ══════════════════════════════════════════════════════════════

def generate_rsa_keypair_only(blockchain_address: str) -> Dict[str, str]:
    """
    Génère une paire RSA-2048 pour la signature des diplômes PDF.
    Lie la clé publique à l'adresse MetaMask via l'empreinte.

    Appelé UNE SEULE FOIS à l'inscription de l'université.

    Args:
        blockchain_address : adresse Ethereum fournie par MetaMask (0x...)

    Returns:
        {
          "private_key_pem"  : clé privée RSA (à stocker côté serveur)
          "public_key_pem"   : clé publique RSA (publique, partageable)
          "crypto_fingerprint": SHA256(adresse_eth + pubkey_rsa_pem)
        }
    """
    # Génération de la clé privée RSA 2048 bits
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    # Dérivation mathématique : clé publique depuis clé privée
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    # Empreinte : SHA256(adresse_metamask + clé_publique_rsa)
    crypto_fingerprint = hashlib.sha256(
        (blockchain_address.lower() + public_pem.strip()).encode("utf-8")
    ).hexdigest()

    return {
        "private_key_pem":   private_pem,
        "public_key_pem":    public_pem,
        "crypto_fingerprint": crypto_fingerprint,
    }


# ══════════════════════════════════════════════════════════════
# 2. HASH SHA-256 (inchangé)
# ══════════════════════════════════════════════════════════════

def hash_file(file_path: str) -> str:
    """SHA-256 d'un fichier sur disque."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def hash_bytes(data: bytes) -> str:
    """SHA-256 de données en mémoire."""
    return hashlib.sha256(data).hexdigest()


# ══════════════════════════════════════════════════════════════
# 3. SIGNATURE RSA (côté serveur — inchangé)
# ══════════════════════════════════════════════════════════════

def sign_diploma_hash(file_hash: str, private_key_pem: str) -> str:
    """
    Signe le hash SHA-256 du PDF avec la clé privée RSA de l'université.
    Cette opération reste CÔTÉ SERVEUR Django.

    Returns: signature base64 (str)
    """
    # Déchiffrement de la clé (Audit Sécurité)
    decrypted_key = decrypt_private_key(private_key_pem)
    
    private_key = serialization.load_pem_private_key(
        decrypted_key.encode("utf-8"),
        password=None,
        backend=default_backend(),
    )
    signature = private_key.sign(
        file_hash.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("utf-8")


# ══════════════════════════════════════════════════════════════
# 4. VÉRIFICATION SIGNATURE RSA (inchangé)
# ══════════════════════════════════════════════════════════════

def verify_diploma_signature(
    file_hash: str,
    signature_b64: str,
    public_key_pem: str,
) -> Tuple[bool, str]:
    """
    Vérifie la signature RSA d'un diplôme.

    Returns:
        (True,  "valid")             → authentique
        (False, "invalid_signature") → faux diplôme
        (False, "error:...")         → erreur technique
    """
    try:
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode("utf-8"),
            backend=default_backend(),
        )
        signature = base64.b64decode(signature_b64)
        public_key.verify(
            signature,
            file_hash.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True, "valid"
    except InvalidSignature:
        return False, "invalid_signature"
    except Exception as e:
        return False, f"error:{str(e)}"


# ══════════════════════════════════════════════════════════════
# 5. VÉRIFICATION SIGNATURE METAMASK (NOUVEAU)
#    Le frontend envoie la signature ETH produite par MetaMask.
#    Django la vérifie sans jamais avoir vu la clé privée.
# ══════════════════════════════════════════════════════════════

def verify_eth_signature_from_metamask(
    message: str,
    eth_signature_hex: str,
    expected_address: str,
) -> Tuple[bool, str]:
    """
    Vérifie qu'une signature Ethereum produite par MetaMask
    correspond bien à l'adresse attendue.
    """
    try:
        from eth_account import Account
        from eth_account.messages import encode_defunct
        from web3 import Web3
        import logging
        logger = logging.getLogger(__name__)

        # Normaliser la signature
        sig = eth_signature_hex
        if not sig.startswith("0x"):
            sig = "0x" + sig

        # Reconstruction du message (hash)
        # On essaie d'abord sans le 0x (le hash pur)
        clean_msg = message[2:] if message.startswith("0x") else message
        signable_message = encode_defunct(text=clean_msg)

        # Récupération de l'adresse depuis la signature
        recovered_address = Account.recover_message(
            signable_message,
            signature=sig,
        )

        # Si ça échoue, on tente AVEC le 0x au cas où le frontend l'aurait inclus
        w3 = Web3()
        recovered_checksum = w3.to_checksum_address(recovered_address)
        expected_checksum = w3.to_checksum_address(expected_address)

        if recovered_checksum != expected_checksum:
            # Deuxième tentative avec 0x
            alt_msg = "0x" + clean_msg
            alt_signable = encode_defunct(text=alt_msg)
            alt_recovered = Account.recover_message(alt_signable, signature=sig)
            recovered_checksum = w3.to_checksum_address(alt_recovered)

        if recovered_checksum == expected_checksum:
            return True, "valid"
        else:
            return False, "address_mismatch"

    except Exception as e:
        return False, f"error:{str(e)}"


# ══════════════════════════════════════════════════════════════
# 6. VALIDATION FORMAT ADRESSE ETHEREUM
# ══════════════════════════════════════════════════════════════

def is_valid_eth_address(address: str) -> bool:
    """
    Vérifie qu'une chaîne est une adresse Ethereum valide (0x + 40 hex chars).
    Utilisé dans le serializer d'inscription.
    """
    import re
    if not address:
        return False
    return bool(re.match(r"^0x[0-9a-fA-F]{40}$", address))


# ══════════════════════════════════════════════════════════════
# 7. CHIFFREMENT DES CLÉS RSA AU REPOS (AUDIT SÉCURITÉ)
# ══════════════════════════════════════════════════════════════

def _get_fernet():
    """Génère une instance Fernet basée sur la SECRET_KEY de Django."""
    # Fernet nécessite une clé de 32 octets encodée en base64 url-safe
    key_seed = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key_seed))

def encrypt_private_key(pem_text: str) -> str:
    """Chiffre la clé privée RSA avant stockage en base de données."""
    if not pem_text:
        return ""
    f = _get_fernet()
    return f.encrypt(pem_text.encode()).decode()

def decrypt_private_key(encrypted_text: str) -> str:
    """Déchiffre la clé privée RSA pour utilisation en mémoire."""
    if not encrypted_text:
        return ""
    # Si le texte ne ressemble pas à du Fernet (gAAAA...), on le renvoie tel quel
    # (Compatibilité avec les anciennes clés en clair)
    if not encrypted_text.startswith("gAAAA"):
        return encrypted_text
    try:
        f = _get_fernet()
        return f.decrypt(encrypted_text.encode()).decode()
    except Exception:
        # En cas d'erreur de déchiffrement, on renvoie le texte original
        return encrypted_text

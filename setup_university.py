import os
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from universities.models import University
from universities.crypto_service import generate_rsa_keypair_only

def setup_ist_university():
    name = "IST"
    email = "ist@example.com"
    password = "password123"
    eth_address = "0xA37e520Fa05c321edbc7d280a0cd870250c1263C"

    print(f"--- Configuration de l'Université {name} ---")

    # 1. Vérifier si elle existe déjà
    if University.objects.filter(email=email).exists():
        print(f"[INFO] L'université {email} existe déjà. Suppression pour réinitialisation...")
        University.objects.filter(email=email).delete()

    # 2. Générer les clés RSA pour cette université
    print(f"[ACTION] Génération des clés cryptographiques...")
    crypto_data = generate_rsa_keypair_only(eth_address)

    # 3. Création de l'utilisateur
    try:
        user = University.objects.create_user(
            email=email,
            password=password,
            name=name,
            country="Burkina Faso",
            acronym="IST",
            blockchain_address=eth_address,
            public_key_pem=crypto_data['public_key_pem'],
            private_key_pem=crypto_data['private_key_pem'],
            crypto_fingerprint=crypto_data['crypto_fingerprint']
        )
        print(f"[OK] Université créée avec succès !")
        print(f"    - Email : {email}")
        print(f"    - Password : {password}")
        print(f"    - Adresse ETH : {eth_address}")
        print("\n[IMPORTANT] Assurez-vous d'utiliser ce compte dans MetaMask pour signer.")
        
    except Exception as e:
        print(f"[ERREUR] Impossible de créer l'université : {e}")

if __name__ == "__main__":
    setup_ist_university()

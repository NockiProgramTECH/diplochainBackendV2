import os
import django
import sys

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from universities.models import University
from universities.crypto_service import generate_rsa_keypair_only
from diplomas.models import Diploma

def reset_and_setup():
    print("=== NETTOYAGE COMPLET ET CONFIGURATION IST ===")
    
    # 1. Nettoyage de la base de données
    print("[1/3] Suppression des données existantes...")
    try:
        # Supprime tous les diplômes et universités
        Diploma.objects.all().delete()
        University.objects.all().delete()
        print("    - Base de données vidée.")
    except Exception as e:
        print(f"    - Erreur lors du nettoyage : {e}")
        return

    # 2. Configuration des données
    name = "IST"
    email = "ist@example.com"
    password = "password123"
    # Utilisation de l'adresse détectée dans vos derniers logs pour éviter address_mismatch
    eth_address = "0x66CB6E339F8f54F97A7A47571D4d6d9972D3C3bA"
    
    print(f"[2/3] Génération des clés pour {name}...")
    try:
        crypto_data = generate_rsa_keypair_only(eth_address)
    except Exception as e:
        print(f"    - Erreur génération clés : {e}")
        return

    # 3. Création de l'université
    print(f"[3/3] Création de l'université {name}...")
    try:
        University.objects.create_user(
            email=email,
            password=password,
            name=name,
            country="Burkina Faso",
            acronym="IST",
            blockchain_address=eth_address,
            public_key_pem=crypto_data['public_key_pem'],
            private_key_pem=crypto_data['private_key_pem'],
            crypto_fingerprint=crypto_data['crypto_fingerprint'],
            is_verified=True # On la marque comme vérifiée pour autoriser l'émission
        )
        print("\n=== CONFIGURATION TERMINÉE AVEC SUCCÈS ===")
        print(f"  - Email : {email}")
        print(f"  - Pass  : {password}")
        print(f"  - Wallet: {eth_address}")
        print("\nUTILISATION :")
        print("1. Dans le HTML, allez directement à LOGIN (ne faites pas Register).")
        print("2. Connectez-vous avec les identifiants ci-dessus.")
        print("3. Assurez-vous que MetaMask est sur le compte 0x66CB...3bA.")
        
    except Exception as e:
        print(f"    - Erreur création université : {e}")

if __name__ == "__main__":
    reset_and_setup()

import os
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from diplomas.models import Diploma
from universities.models import University

def debug_diplomas():
    print("--- Diagnostic des Diplômes ---")
    diplomas = Diploma.objects.all()
    if not diplomas.exists():
        print("[INFO] Aucun diplôme trouvé en base de données.")
        return

    for d in diplomas:
        print(f"Diplôme ID: {d.id}")
        print(f"  - Étudiant: {d.student_dob}")
        print(f"  - Université: {d.university.name} ({d.university.email})")
        print(f"  - Statut: {d.status}")
        print(f"  - Hash: {d.file_hash}")
        print("-" * 30)

    universities = University.objects.all()
    print("\n--- Universités en base ---")
    for u in universities:
        print(f"ID: {u.id} | Nom: {u.name} | Email: {u.email} | Wallet: {u.blockchain_address}")

if __name__ == "__main__":
    debug_diplomas()

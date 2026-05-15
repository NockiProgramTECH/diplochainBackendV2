"""
Script appelé pendant le build Render pour créer/mettre à jour le compte admin.
Usage : python create_admin.py
"""
import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.hashers import make_password
from universities.models import University

email = os.environ.get("ADMIN_EMAIL", "admin@gmail.com")
password = make_password(os.environ.get("ADMIN_PASSWORD", "1234"))

updated = University.objects.filter(email=email).update(
    password=password,
    is_staff=True,
    is_superuser=True,
    is_active=True,
)

if updated:
    print(f"[create_admin] Compte mis à jour : {email}")
    sys.exit(0)

# L'utilisateur n'existe pas encore — insertion directe via SQL
import uuid
from django.db import connection

try:
    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO universities_university
              (id, email, name, acronym, country, city, website,
               password, is_active, is_staff, is_superuser, is_verified,
               blockchain_address, private_key_pem, public_key_pem,
               crypto_fingerprint, date_joined)
            VALUES
              (%s, %s, %s, %s, %s, %s, %s,
               %s, %s, %s, %s, %s,
               %s, %s, %s,
               %s, NOW())
            """,
            [
                str(uuid.uuid4()),
                email,
                "Admin DiploChain",
                "ADM",
                "Burkina Faso",
                "Ouagadougou",
                None,
                password,
                True, True, True, False,
                "",  # blockchain_address vide
                "", "",
                "",
            ],
        )
    print(f"[create_admin] Compte créé : {email}")
except Exception as e:
    print(f"[create_admin] Erreur : {e}", file=sys.stderr)
    sys.exit(1)

import os, sys, django

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
    print(f"[admin] mis a jour : {email}")
    sys.exit(0)

from django.db import connection
import uuid

with connection.cursor() as c:
    c.execute(
        "INSERT INTO universities_university "
        "(id,email,name,acronym,country,city,website,password,is_active,is_staff,"
        "is_superuser,is_verified,blockchain_address,private_key_pem,public_key_pem,"
        "crypto_fingerprint,date_joined) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())",
        [str(uuid.uuid4()), email, "Admin DiploChain", "ADM",
         "Burkina Faso", "Ouagadougou", None, password,
         True, True, True, False, "", "", "", ""],
    )
print(f"[admin] cree : {email}")

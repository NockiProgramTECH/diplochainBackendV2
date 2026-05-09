from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import University


@admin.register(University)
class UniversityAdmin(UserAdmin):
    list_display  = ["name", "acronym", "email", "blockchain_address",
                     "is_verified", "is_active", "wallet_connected_at", "date_joined"]
    list_filter   = ["is_verified", "is_active", "country"]
    search_fields = ["name", "email", "acronym", "blockchain_address"]
    ordering      = ["-date_joined"]

    fieldsets = (
        ("Informations",      {"fields": ("email", "name", "acronym", "country", "city", "website", "logo")}),
        ("Clés RSA (Django)", {"fields": ("public_key_pem", "private_key_pem"), "classes": ("collapse",)}),
        ("Wallet MetaMask",   {"fields": ("blockchain_address", "wallet_connected_at", "crypto_fingerprint")}),
        ("Statut",            {"fields": ("is_active", "is_verified", "is_staff", "is_superuser")}),
        ("Permissions",       {"fields": ("groups", "user_permissions"), "classes": ("collapse",)}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": (
            "email", "name", "acronym", "country",
            "blockchain_address", "password1", "password2"
        )}),
    )
    readonly_fields = ["crypto_fingerprint", "public_key_pem", "wallet_connected_at"]

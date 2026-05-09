"""
universities/urls.py — Routes mises à jour pour MetaMask
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # ── Authentification ──────────────────────────────────────
    path("auth/register/",         views.RegisterUniversityView.as_view(), name="university-register"),
    path("auth/login/",            TokenObtainPairView.as_view(),          name="university-login"),
    path("auth/token/refresh/",    TokenRefreshView.as_view(),             name="token-refresh"),
    path("auth/profile/",          views.MyProfileView.as_view(),          name="university-profile"),
    path("auth/keys/",             views.MyKeysView.as_view(),             name="university-keys"),

    # ── Wallet MetaMask — NOUVEAU ─────────────────────────────
    # Étape 1 : récupérer le challenge à signer
    path("auth/wallet-challenge/", views.WalletChallengeView.as_view(),   name="wallet-challenge"),
    # Étape 2 : soumettre l'adresse + la signature MetaMask
    path("auth/connect-wallet/",   views.ConnectWalletView.as_view(),     name="connect-wallet"),

    # ── Public ────────────────────────────────────────────────
    path("universities/",          views.UniversityListView.as_view(),     name="university-list"),
    path("universities/<uuid:pk>/",views.UniversityPublicDetailView.as_view(), name="university-detail"),
]

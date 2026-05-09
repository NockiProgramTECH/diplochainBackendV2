"""
diplomas/urls.py — Routes mises à jour MetaMask
"""
from django.urls import path
from . import views

urlpatterns = [
    # Émission — étape 1/2 : Django génère PDF + hash + signature RSA
    path("diplomas/issue/",
         views.DiplomaIssueView.as_view(),
         name="diploma-issue"),

    # Émission — étape 2/2 : NOUVEAU — reçoit la signature MetaMask
    path("diplomas/<uuid:pk>/confirm-eth-sig/",
         views.ConfirmEthSigView.as_view(),
         name="diploma-confirm-eth-sig"),

    # Ancrage blockchain — étape 3 facultative (persistance immuable)
    path("diplomas/<uuid:pk>/anchor/",
         views.AnchorDiplomaView.as_view(),
         name="diploma-anchor"),

    # Liste (université connectée)
    path("diplomas/",
         views.MyDiplomasView.as_view(),
         name="diploma-list"),

    # Détail public
    path("diplomas/<uuid:pk>/",
         views.DiplomaDetailView.as_view(),
         name="diploma-detail"),

    # Révocation
    path("diplomas/<uuid:pk>/revoke/",
         views.RevokeDiplomaView.as_view(),
         name="diploma-revoke"),

    # Vérification publique
    path("diplomas/verify/file/",
         views.VerifyByFileView.as_view(),
         name="diploma-verify-file"),

    path("diplomas/verify/hash/",
         views.VerifyByHashView.as_view(),
         name="diploma-verify-hash"),
]

# Audit de Sécurité et de Mise en Production — DiploChain API

Ce document résume l'audit de sécurité et de robustesse effectué sur l'API DiploChain.

## 1. Sécurité Critique (Action Requise Immédiate)

| Risque | Fichier(s) | Description | État |
| :--- | :--- | :--- | :--- |
| **DEBUG=True** | `.env` | Le mode debug est activé. | ⚠️ En attente (volontaire) |
| **Permissions Ouvertes** | `diplomas/views.py` | `ConfirmEthSigView` utilisait `AllowAny`. | ✅ Corrigé (IsAuthenticated) |
| **Exposition Clé Privée** | `universities/views.py` | `MyKeysView` retournait la clé privée RSA. | ✅ Corrigé (Exclusion de la réponse) |
| **Clés RSA non chiffrées** | `universities/crypto_service.py` | Les clés RSA étaient stockées en clair. | ✅ Corrigé (Chiffrement Fernet au repos) |
| **CORS permissif** | `config/settings.py` | `CORS_ALLOW_ALL_ORIGINS = True`. | ✅ Corrigé (Restreint) |

## 2. Configuration de Production

### 2.1 Base de données
- **Actuel** : SQLite (`db.sqlite3`).
- **Audit** : SQLite n'est pas adapté à la production (concurrence, robustesse).
- **Action** : Migrer vers **PostgreSQL** ou **MySQL**.

### 2.2 Variables d'Environnement (`.env`)
- **SECRET_KEY** : La clé actuelle est un placeholder (`django-insecure-...`).
- **ALLOWED_HOSTS** : Actuellement limité à `localhost`. Ajoutez le nom de domaine de production.
- **BLOCKCHAIN_PRIVATE_KEY** : Stockée en texte brut dans le `.env`. Assurez-vous que le fichier `.env` a des permissions restrictives (`600`).

## 3. Analyse du Code Source

### Points Forts
- Utilisation de **JWT** pour l'authentification.
- Validation des entrées via les **Serializers**.
- Double signature (RSA serveur + MetaMask client) solide.

3.  **Throttling** : Configuré (1000 req/jour pour les universités).
4.  **Expiration Challenge** : Implémentée (5 minutes).
5.  **Logging** : Nettoyé pour la production.

## 4. Conclusion

> [!IMPORTANT]
> **L'API est désormais beaucoup plus proche d'un état "Production Ready".**
> Les risques majeurs ont été mitigés. Il reste principalement le passage à une base de données robuste (PostgreSQL) et la désactivation du mode Debug.

### Score Global : 8/10 (Risque Faible)

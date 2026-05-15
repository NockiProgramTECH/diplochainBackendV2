# DiploChain — Backend Django

![Version](https://img.shields.io/badge/version-1.0.0--beta-blue?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg?style=flat-square)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Django](https://img.shields.io/badge/django-%23092e20.svg?style=for-the-badge&logo=django&logoColor=white)
![Django REST Framework](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white)
![Polygon](https://img.shields.io/badge/Polygon-8247E5?style=for-the-badge&logo=polygon&logoColor=white)
![Ethereum](https://img.shields.io/badge/Ethereum-3C3C3D?style=for-the-badge&logo=ethereum&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=JSON%20web%20tokens)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)
![Swagger](https://img.shields.io/badge/-Swagger-%2385EA2D?style=for-the-badge&logo=swagger&logoColor=black)
![Gunicorn](https://img.shields.io/badge/gunicorn-%232980b9.svg?style=for-the-badge&logo=gunicorn&logoColor=white)

Système de certification et de vérification de diplômes par cryptographie (RSA) et blockchain (Polygon).  
Développé pour le contexte burkinabè (MIABE Hackathon 2026 — Equipe-BF-10).

---

## 📌 Sommaire
- [🌟 Présentation](#-présentation)
- [🚀 Fonctionnalités Clés](#-fonctionnalités-clés)
- [🛠️ Stack Technique](#️-stack-technique)
- [⚙️ Configuration et Installation](#️-configuration-et-installation)
- [📄 Configuration .env](#-configuration-env)
- [🏗️ Architecture des Clés](#️-architecture-des-clés)
- [🔄 Workflow d'émission](#-workflow-démission)
- [📚 Documentation API](#-documentation-api)
- [🛡️ Sécurité Blockchain](#️-sécurité-blockchain)

---

## 🌟 Présentation

DiploChain est une infrastructure logicielle permettant aux universités de délivrer des diplômes numériques infalsifiables. Chaque diplôme est signé cryptographiquement par l'université émettrice et ancré sur la blockchain Polygon pour garantir son immuabilité et sa vérifiabilité universelle sans intermédiaire.

---

## 🚀 Fonctionnalités Clés

- **Gestion des Universités** : Inscription sécurisée, gestion des profils et génération automatique de paires de clés (RSA pour la signature de fichiers et Ethereum pour la blockchain).
- **Émission de Diplômes** : Processus complet incluant la génération de PDF sécurisés avec QR Code, double signature (RSA + ECDSA) et hachage SHA-256.
- **Ancrage Blockchain** : Publication de l'empreinte numérique du diplôme sur le réseau **Polygon Amoy** via un Smart Contract sécurisé.
- **Vérification Multi-mode** :
  - **Par fichier** : Analyse du PDF pour extraire le hash et vérifier les signatures.
  - **Par hash** : Recherche directe dans la base de données et sur la blockchain.
  - **Temps réel** : Interrogation directe du Smart Contract pour confirmer l'ancrage.
- **API d'Administration** : CRUD complet pour les administrateurs système sur les universités et les diplômes.
- **Réinitialisation de mot de passe** : Système sécurisé par code de vérification envoyé par email.

---

## 🛠️ Stack Technique

- **Backend** : Django 4.2, Django REST Framework.
- **Base de données** : SQLite (développement) / PostgreSQL (production).
- **Cryptographie** : RSA-2048 (RSA-PSS), ECDSA (secp256k1 via `web3.py`).
- **Blockchain** : Polygon Amoy Testnet (Smart Contract Solidity).
- **PDF** : ReportLab avec intégration de QR Codes.
- **Authentification** : JWT (JSON Web Tokens).

---

## ⚙️ Configuration et Installation

### 1. Prérequis
- Python 3.10+
- Un portefeuille MetaMask avec du MATIC de test (Amoy) pour le déploiement/ancrage.

### 2. Installation
```bash
# Cloner le projet
git clone <votre-repo>
cd diplochainbackend

# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos paramètres (clés API, RPC, etc.)
```

### 3. Base de données
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Lancement
```bash
python manage.py runserver
```

---

## 📄 Configuration du fichier .env

| Variable | Description | Exemple |
|---|---|---|
| `SECRET_KEY` | Clé secrète Django | `django-insecure-...` |
| `DEBUG` | Mode debug | `True` |
| `BLOCKCHAIN_RPC_URL` | URL du nœud Polygon | `https://rpc-amoy.polygon.technology` |
| `CONTRACT_ADDRESS` | Adresse du Smart Contract | `0x...` |
| `BLOCKCHAIN_PRIVATE_KEY`| Clé privée du serveur (Gas Station) | `...` |
| `EMAIL_BACKEND` | Gestion des emails | `django.core.mail.backends.console.EmailBackend` |

---

## 🏗️ Architecture des Clés

Chaque université dispose de :
1. **Clé RSA-2048** : Utilisée pour signer le contenu du PDF. La signature est incluse dans les métadonnées du document.
2. **Clé Ethereum (secp256k1)** : Utilisée pour prouver l'identité sur la blockchain.
3. **Fingerprint** : Une empreinte unique combinant les clés publiques, agissant comme identifiant cryptographique immuable.

---

## 🔄 Workflow d'émission d'un diplôme

Le processus est divisé en 4 étapes pour garantir une sécurité maximale :

1. **Issue** (`POST /api/diplomas/issue/`) : L'université soumet les données de l'étudiant. Le serveur génère le PDF et calcule le hash SHA-256.
2. **MetaMask Sign** : Le frontend demande à l'utilisateur de signer le hash avec son compte MetaMask (prouve l'identité de l'émetteur).
3. **Confirm** (`POST /api/diplomas/{id}/confirm-eth-sig/`) : La signature MetaMask est envoyée au serveur pour validation et stockage.
4. **Anchor** (`POST /api/diplomas/{id}/anchor/`) : Le serveur publie le hash sur la blockchain Polygon.

---

## 📚 Documentation API

### Authentification & Profils
- `POST /api/auth/register/` : Inscription d'une université.
- `POST /api/auth/login/` : Connexion et obtention des tokens JWT.
- `POST /api/auth/password-reset/request/` : Demander un code de réinitialisation.
- `POST /api/auth/password-reset/confirm/` : Valider le code et changer le mot de passe.
- `GET /api/auth/profile/` : Voir son profil université.

### Diplômes (Usage Université)
- `POST /api/diplomas/issue/` : Créer un diplôme (draft).
- `GET /api/diplomas/` : Liste des diplômes émis.
- `POST /api/diplomas/{id}/revoke/` : Révoquer un diplôme.
- `POST /api/diplomas/{id}/anchor/` : Lancer l'ancrage blockchain.

### Vérification (Public)
- `POST /api/diplomas/verify/file/` : Upload d'un PDF pour vérification complète.
- `POST /api/diplomas/verify/hash/` : Vérification par hash SHA-256.

### Administration (Staff uniquement)
- `GET /api/admin/diplomas/` : Liste globale des diplômes.
- `GET /api/admin/universities/` : Liste globale des universités.
- Accès complet aux opérations CRUD.

---

## 🖥️ Scripts utilitaires

- `reset_and_setup.py` : Réinitialise la base de données et crée un environnement de test propre.
- `setup_university.py` : Script rapide pour configurer une université de test.
- `check_blockchain.py` : Vérifie manuellement l'existence d'un hash sur le Smart Contract.
- `debug_diplomas.py` : Analyse les données des diplômes en base pour le débogage.

---

## 🛡️ Sécurité de la Blockchain

Le Smart Contract `DiplomaRegistry.sol` vérifie systématiquement que la signature soumise correspond à l'adresse de l'université déclarée. Le serveur DiploChain agit comme un "Gas Station" : il paie les frais de transaction, mais l'autorité de certification reste détenue par la clé privée de l'université (via MetaMask).

---

## 📝 Licence

Ce projet est développé dans le cadre du **MIABE Hackathon 2026**.  
Équipe-BF-10.

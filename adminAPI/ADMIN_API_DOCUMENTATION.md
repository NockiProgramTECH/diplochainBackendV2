# Documentation API Admin — DiploChain

Cette documentation décrit l'API d'administration dédiée aux opérations CRUD sur les diplômes et universités.

## Base URL

- `https://<host>/api/admin/`

> Cette API est protégée et réservée aux utilisateurs administrateurs (`is_staff=True`).

## Authentification requise

- Authentification via JWT
- Header HTTP : `Authorization: Bearer <access_token>`

> Les tokens sont fournis par l'API d'authentification existante, par exemple `POST /api/auth/login/`.

---

## Endpoints disponibles

### 1. Diplômes

| Méthode | URL | Action |
|---|---|---|
| GET | `/api/admin/diplomas/` | Lister tous les diplômes |
| POST | `/api/admin/diplomas/` | Créer un diplôme |
| GET | `/api/admin/diplomas/{id}/` | Récupérer un diplôme par son UUID |
| PUT | `/api/admin/diplomas/{id}/` | Remplacer un diplôme existant |
| PATCH | `/api/admin/diplomas/{id}/` | Mettre à jour partiellement un diplôme |
| DELETE | `/api/admin/diplomas/{id}/` | Supprimer un diplôme |

#### Schéma du diplôme

Champs renvoyés / acceptés par l'API :

- `id` (UUID, lecture seule)
- `university` (UUID de l'université émettrice)
- `university_name` (string, lecture seule)
- `university_acronym` (string, lecture seule)
- `student_first_name` (string)
- `student_last_name` (string)
- `student_dob` (date, format `YYYY-MM-DD`)
- `student_national_id` (string)
- `degree_title` (string)
- `degree_level` (string)
- `field_of_study` (string)
- `mention` (string)
- `graduation_year` (entier)
- `pdf_file` (URL de fichier ou `null`)
- `file_hash` (string)
- `rsa_signature` (string)
- `university_fingerprint_at_issue` (string)
- `eth_signature` (string)
- `eth_message_hash` (string)
- `blockchain_tx_hash` (string)
- `blockchain_block_number` (entier ou `null`)
- `status` (string)
- `is_revoked` (bool)
- `revocation_reason` (string)
- `issued_at` (datetime)
- `updated_at` (datetime)

> Pour la création et la modification, inclure uniquement les champs écrits. Les champs calculés ou spécifiques à la blockchain peuvent rester vides si l'opération ne les met pas à jour.

#### Exemple : création d'un diplôme

```http
POST /api/admin/diplomas/
Authorization: Bearer <token>
Content-Type: application/json

{
  "university": "d9de4b6a-0c0f-4c30-9b3a-ea1e7a1b2bb0",
  "student_first_name": "Aïssata",
  "student_last_name": "Ouédraogo",
  "student_dob": "2001-04-12",
  "student_national_id": "BF12345678",
  "degree_title": "Licence en Informatique",
  "degree_level": "licence",
  "field_of_study": "Informatique",
  "mention": "bien",
  "graduation_year": 2025,
  "status": "draft"
}
```

#### Exemple : réponse de création / lecture

```json
{
  "id": "ce5d2ed7-2b7e-4f1e-8f54-7b67f196d8c4",
  "university": "d9de4b6a-0c0f-4c30-9b3a-ea1e7a1b2bb0",
  "university_name": "Université de Ouagadougou",
  "university_acronym": "UO",
  "student_first_name": "Aïssata",
  "student_last_name": "Ouédraogo",
  "student_dob": "2001-04-12",
  "student_national_id": "BF12345678",
  "degree_title": "Licence en Informatique",
  "degree_level": "licence",
  "field_of_study": "Informatique",
  "mention": "bien",
  "graduation_year": 2025,
  "pdf_file": null,
  "file_hash": "",
  "rsa_signature": "",
  "university_fingerprint_at_issue": "",
  "eth_signature": "",
  "eth_message_hash": "",
  "blockchain_tx_hash": "",
  "blockchain_block_number": null,
  "status": "draft",
  "is_revoked": false,
  "revocation_reason": "",
  "issued_at": "2026-05-15T12:00:00Z",
  "updated_at": "2026-05-15T12:00:00Z"
}
```

### 2. Universités

| Méthode | URL | Action |
|---|---|---|
| GET | `/api/admin/universities/` | Lister toutes les universités |
| POST | `/api/admin/universities/` | Créer une université |
| GET | `/api/admin/universities/{id}/` | Récupérer une université |
| PUT | `/api/admin/universities/{id}/` | Mettre à jour une université |
| PATCH | `/api/admin/universities/{id}/` | Mettre à jour partiellement une université |
| DELETE | `/api/admin/universities/{id}/` | Supprimer une université |

#### Schéma de l'université

Champs disponibles :

- `id` (UUID)
- `email` (string)
- `name` (string)
- `acronym` (string)
- `country` (string)
- `city` (string)
- `website` (URL)
- `logo` (URL de l'image ou `null`)
- `private_key_pem` (string, écriture seule)
- `public_key_pem` (string)
- `blockchain_address` (string, adresse Ethereum)
- `wallet_connected_at` (datetime ou `null`)
- `crypto_fingerprint` (string)
- `is_active` (bool)
- `is_staff` (bool)
- `is_superuser` (bool)
- `is_verified` (bool)
- `date_joined` (datetime)
- `password` (écriture seule)

> `password` est write-only et n'est pas renvoyé dans les réponses.
> `private_key_pem` est aussi write-only pour des raisons de sécurité.

#### Exemple : création d'une université

```http
POST /api/admin/universities/
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "contact@uo.bf",
  "name": "Université de Ouagadougou",
  "acronym": "UO",
  "country": "Burkina Faso",
  "city": "Ouagadougou",
  "website": "https://uo.bf",
  "password": "SuperSecret123",
  "public_key_pem": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----",
  "private_key_pem": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----",
  "blockchain_address": "0x1234567890abcdef1234567890abcdef12345678",
  "is_staff": false,
  "is_verified": false
}
```

#### Exemple : réponse de création / lecture

```json
{
  "id": "f8b19f2d-4417-4a9c-a60c-075426931b9e",
  "email": "contact@uo.bf",
  "name": "Université de Ouagadougou",
  "acronym": "UO",
  "country": "Burkina Faso",
  "city": "Ouagadougou",
  "website": "https://uo.bf",
  "logo": null,
  "public_key_pem": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----",
  "blockchain_address": "0x1234567890ABCDEF1234567890ABCDEF12345678",
  "wallet_connected_at": null,
  "crypto_fingerprint": "2b6a5f...",
  "is_active": true,
  "is_staff": false,
  "is_superuser": false,
  "is_verified": false,
  "date_joined": "2026-05-15T12:00:00Z"
}
```

---

## Comportement spécifique

- Les opérations sont disponibles uniquement pour les utilisateurs administrateurs (`IsAdminUser`).
- Les listes renvoient une collection d'objets JSON.
- Les `PUT` attendent un objet complet ; les `PATCH` permettent des mises à jour partielles.
- Les `DELETE` suppriment définitivement l'objet.

## Erreurs courantes

- `401 Unauthorized` : jeton absent ou invalide.
- `403 Forbidden` : l'utilisateur n'est pas administrateur.
- `400 Bad Request` : données de requête incorrectes ou format invalide.
- `404 Not Found` : identifiant invalide.

## Conseils pour le frontend

1. Utiliser un admin utilisateur pour tester les routes.
2. Récupérer le token JWT via le endpoint `POST /api/auth/login/`.
3. Inclure `Authorization: Bearer <token>` pour toutes les requêtes vers `/api/admin/`.
4. Traiter `logo` et `pdf_file` comme des URL de fichier renvoyées par Django.
5. Lire les messages d'erreur JSON renvoyés par DRF pour afficher les validations.

---

## Notes

- L'API admin ne gère que les opérations CRUD sur les modèles `Diploma` et `University`.
- Les champs de signature et de blockchain sont exposés mais peuvent être laissés vides lors de la création initiale.
- Pour la création de diplômes, le champ `university` doit contenir l'UUID d'une université existante.

# Documentation API — Réinitialisation de mot de passe

Cette documentation décrit les endpoints de réinitialisation de mot de passe pour les comptes `University`.

## Base URL

- URL racine : `https://<host>/api/auth/`

## Authentification

- Ces endpoints ne nécessitent pas d'authentification.
- Ils fonctionnent uniquement avec l'adresse e-mail enregistrée.

---

## 1. Demande d'envoi du code de réinitialisation

### Endpoint

- `POST /api/auth/password-reset/request/`

### Description

Demande l'envoi d'un code à 6 chiffres par email à l'adresse fournie.
Si l'e-mail existe dans la base, un code valide 30 minutes est créé et envoyé.
Le message de réponse reste générique pour des raisons de sécurité.

### Requête

Headers :
- `Content-Type: application/json`

Body :

```json
{
  "email": "admin@uo.bf"
}
```

### Réponse

Code HTTP : `200 OK`

Body :

```json
{
  "message": "Si cet e-mail est enregistré, un code de réinitialisation a été envoyé. Vérifiez votre boîte de réception."
}
```

### Notes frontend

- Afficher un message neutre même si l'e-mail n'existe pas.
- Le code est envoyé par e-mail et reste valide 30 minutes.
- Le backend marque les anciens codes non utilisés comme invalides à chaque nouvelle demande.

---

## 2. Confirmation du code et définition d'un nouveau mot de passe

### Endpoint

- `POST /api/auth/password-reset/confirm/`

### Description

Valide le code envoyé par e-mail et met à jour le mot de passe si le code est correct.

### Requête

Headers :
- `Content-Type: application/json`

Body :

```json
{
  "email": "admin@uo.bf",
  "code": "123456",
  "password": "NouveauMotDePasse123!",
  "password_confirm": "NouveauMotDePasse123!"
}
```

### Réponse en cas de succès

Code HTTP : `200 OK`

Body :

```json
{
  "message": "Le mot de passe a été réinitialisé avec succès."
}
```

### Réponses d'erreur possibles

- `400 Bad Request` si :
  - l'e-mail n'est pas enregistré,
  - le code est incorrect,
  - le code a expiré,
  - les mots de passe ne correspondent pas,
  - le mot de passe ne respecte pas les règles de validation Django.

Exemple d'erreur :

```json
{
  "detail": "Adresse e-mail ou code invalide."
}
```

---

## Règles et comportement

- Le code est un nombre à 6 chiffres.
- Il est valide 30 minutes après sa génération.
- Un code ne peut être utilisé qu'une seule fois.
- Si un nouvel email de réinitialisation est demandé, les anciens codes actifs sont rendus invalides.
- Le mot de passe est enregistré avec `set_password()` et respecte les validateurs de Django.

## Configuration email

Le backend envoie déjà le code à l'adresse e-mail de l'utilisateur via Django `send_mail()`.

En développement, Django utilise par défaut la console si `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` :
- le code apparaît dans la console, mais il n'est pas envoyé à une vraie boîte mail.

### Pour envoyer les e-mails vers une vraie boîte en dev

Configurez ces variables dans votre `.env` ou votre environnement :

- `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`
- `EMAIL_HOST=localhost` (ou l'hôte SMTP que vous utilisez)
- `EMAIL_PORT=1025` (ou le port SMTP de votre service)
- `EMAIL_HOST_USER=` (vide si non requis)
- `EMAIL_HOST_PASSWORD=` (vide si non requis)
- `DEFAULT_FROM_EMAIL=no-reply@diplochain.local`

### Exemple avec MailHog

```text
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=1025
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=no-reply@diplochain.local
```

Dans ce cas, ouvrez MailHog dans le navigateur (par exemple `http://localhost:8025`) pour lire les messages envoyés.

### Exemple avec un SMTP réel

```text
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=ton.email@gmail.com
EMAIL_HOST_PASSWORD=mot_de_passe_application
DEFAULT_FROM_EMAIL=no-reply@diplochain.local
```

## Configuration en production

En production, il faut utiliser un service SMTP réel et sécurisé, pas la console.

- `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`
- `EMAIL_HOST` : serveur SMTP fourni par ton service email ou ton hébergeur
- `EMAIL_PORT` : généralement `587` pour TLS ou `465` pour SSL
- `EMAIL_USE_TLS=True` ou `EMAIL_USE_SSL=True` selon le service
- `EMAIL_HOST_USER` : ton identifiant SMTP
- `EMAIL_HOST_PASSWORD` : ton mot de passe SMTP ou mot de passe d'application
- `DEFAULT_FROM_EMAIL` : adresse d'expéditeur (ex: `no-reply@tondomaine.com`)

Exemples de fournisseurs pour la production :
- SendGrid
- Mailgun
- Amazon SES
- SMTP de ton hébergeur
- Gmail avec mot de passe d'application (pas recommandé pour production)

### Exemple de production avec EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=ton.email@gmail.com
EMAIL_HOST_PASSWORD=mot_de_passe_d_application
DEFAULT_FROM_EMAIL=no-reply@tondomaine.com

```text
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=ton_cle_sendgrid
DEFAULT_FROM_EMAIL=no-reply@tondomaine.com
```

### Vérifications importantes

- Assure-toi que `DEFAULT_FROM_EMAIL` utilise un domaine valide et autorisé.
- En production, n'utilise jamais `console.EmailBackend`.
- Si ton service SMTP supporte le TLS, active `EMAIL_USE_TLS=True`.
- Stocke toujours les identifiants SMTP dans des variables d'environnement sécurisées.

## Points de vigilance pour le frontend

- Utiliser un formulaire séparé pour la demande de code et la confirmation.
- Vérifier localement que `password` et `password_confirm` correspondent avant l'envoi.
- Afficher un message clair indiquant que l'e-mail peut mettre quelques minutes à arriver.
- Gérer les erreurs `400` en affichant un message générique sans exposer l'existence de l'e-mail.

# 🎓 Guide DiploChain : La Blockchain pour tous

![Beginner Friendly](https://img.shields.io/badge/beginner-friendly-brightgreen?style=flat-square)
![MetaMask](https://img.shields.io/badge/MetaMask-Supported-orange?style=flat-square&logo=metamask)
![Polygon](https://img.shields.io/badge/Network-Polygon%20Amoy-8247E5?style=flat-square&logo=polygon&logoColor=white)

Ce guide est destiné aux utilisateurs (administrateurs d'université, étudiants, employeurs) qui souhaitent comprendre et utiliser DiploChain sans avoir de connaissances techniques préalables en blockchain.

---

## 🧐 C'est quoi la Blockchain dans DiploChain ?

Imaginez un **grand registre public et indestructible** où l'on note que "Tel diplôme appartient à telle personne et a été signé par telle université". 
- **Personne ne peut effacer** ce qui est écrit.
- **Tout le monde peut vérifier** l'information.
- Cela garantit que le diplôme n'est pas un faux.

---

## 🛠️ Étape 1 : Installer votre "Portefeuille" (MetaMask)

Pour interagir avec la blockchain, vous avez besoin d'un outil appelé **MetaMask**. C'est une extension pour votre navigateur (Chrome, Brave, Firefox).

1. Allez sur [metamask.io](https://metamask.io/) et cliquez sur **Download**.
2. Installez l'extension.
3. **Créez un nouveau portefeuille**. 
   - ⚠️ **IMPORTANT** : Notez bien votre "Phrase de récupération" (12 mots) sur un papier et cachez-le. Ne la donnez JAMAIS à personne.

---

## 🌐 Étape 2 : Se connecter au réseau Polygon Amoy

Par défaut, MetaMask est sur le réseau "Ethereum". DiploChain utilise **Polygon Amoy** (un réseau de test gratuit).

1. Ouvrez MetaMask.
2. Cliquez sur le sélecteur de réseau en haut à gauche.
3. Cliquez sur **Ajouter un réseau** > **Ajouter manuellement**.
4. Remplissez avec ces infos :
   - **Nom du réseau** : Polygon Amoy
   - **Nouvelle URL de RPC** : `https://rpc-amoy.polygon.technology`
   - **ID de chaîne** : `80002`
   - **Symbole** : `MATIC`
   - **URL de l'explorateur** : `https://amoy.polygonscan.com/`

---

## 💰 Étape 3 : Obtenir des jetons gratuits (Faucet)

Sur la blockchain, chaque action (comme certifier un diplôme) coûte une fraction de centime en "gaz". Puisque nous sommes sur un réseau de test, vous pouvez obtenir cet argent gratuitement.

1. Copiez votre adresse MetaMask (elle commence par `0x...`).
2. Allez sur le [Polygon Faucet](https://faucet.polygon.technology/).
3. Collez votre adresse et cliquez sur **Submit**.
4. Attendez 1 minute : vous recevrez du MATIC de test.

---

## 🎓 Étape 4 : Comment certifier un diplôme (Pour l'Université)

Une fois connecté à l'interface DiploChain :

1. **Remplir les informations** : Entrez le nom de l'étudiant et son diplôme. Cliquez sur "Émettre".
2. **Signer (Signature Numérique)** : Une fenêtre MetaMask va s'ouvrir. Elle vous demande de "Signer". Cela prouve que c'est bien votre université qui crée ce document. Cliquez sur **Signer**.
3. **Ancrer sur la Blockchain** : Cliquez sur le bouton "Anchor" (Ancrer). MetaMask s'ouvrira à nouveau pour confirmer la transaction. 
   - *Félicitations ! Le diplôme est désormais gravé dans la pierre numérique.*

---

## 🔍 Étape 5 : Comment vérifier un diplôme (Pour tous)

N'importe qui peut vérifier un diplôme sans avoir besoin de compte.

1. Allez sur la page **Vérification** de DiploChain.
2. **Déposez le fichier PDF** du diplôme reçu.
3. Le système va :
   - Lire la signature de l'université.
   - Vérifier sur la blockchain si l'empreinte correspond.
   - Afficher un message **VERT** (Authentique) ou **ROUGE** (Faux/Modifié).

---

## ❓ FAQ Rapide

- **Est-ce que mes données privées sont sur la blockchain ?**
  Non. Seule une "empreinte numérique" (une suite de lettres et chiffres appelée *Hash*) est stockée. Il est impossible de retrouver le nom de l'étudiant à partir du Hash seul.
- **Pourquoi MetaMask ?**
  C'est votre carte d'identité numérique. Elle remplace le cachet physique de l'université.
- **Combien ça coûte ?**
  Sur le réseau Amoy, c'est totalement gratuit. En production (réseau Polygon réel), cela coûte moins de 0,01 € par diplôme.

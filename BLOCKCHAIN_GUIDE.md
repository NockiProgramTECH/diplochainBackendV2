# Guide d'Intégration Blockchain (Polygon Amoy) — SÉCURISÉ

Ce guide explique comment configurer et utiliser l'ancrage blockchain pour DiploChain en utilisant une architecture de signature on-chain.

## 1. Déploiement du Smart Contract Sécurisé

Le nouveau contrat utilise `msg.sender` et vérifie la signature de l'université directement sur la blockchain. Cela empêche toute usurpation, même si le backend est compromis.

1.  Allez sur [Remix IDE](https://remix.ethereum.org/).
2.  Utilisez le fichier `DiplomaRegistry.sol` (que j'ai créé à la racine) ou copiez ce code :
    ```solidity
    // SPDX-License-Identifier: MIT
    pragma solidity ^0.8.20;

    // Utilisation des URLs GitHub pour que Remix puisse les télécharger automatiquement
    import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/utils/cryptography/ECDSA.sol";
    import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/utils/cryptography/MessageHashUtils.sol";

    contract DiplomaRegistry {
        using ECDSA for bytes32;
        using MessageHashUtils for bytes32;

        struct Diploma {
            bytes32 fileHash;
            address university;
            uint256 timestamp;
            bool exists;
        }

        mapping(bytes32 => Diploma) public diplomas;
        event DiplomaAnchored(bytes32 indexed fileHash, address indexed university, uint256 timestamp);

        function anchorDiploma(bytes32 _fileHash, bytes calldata _signature, address _university) public {
            require(!diplomas[_fileHash].exists, "Deja ancre");
            bytes32 signedMessageHash = _fileHash.toEthSignedMessageHash();
            address signer = signedMessageHash.recover(_signature);
            require(signer == _university, "Signature invalide");

            diplomas[_fileHash] = Diploma(_fileHash, _university, block.timestamp, true);
            emit DiplomaAnchored(_fileHash, _university, block.timestamp);
        }
    }
    ```
3.  Compilez le contrat (Ctrl+S).
4.  Dans l'onglet "Deploy", choisissez l'environnement **Injected Provider - MetaMask**.
5.  Assurez-vous que votre MetaMask est sur le réseau **Polygon Amoy**.
6.  Cliquez sur **Deploy**.
7.  **Notez l'adresse du contrat** (ex: `0x123...`).

## 2. Configuration du Portefeuille Serveur (Gas Station)

Le serveur a besoin d'un portefeuille pour payer les frais de transaction (Gas).

1.  Créez un nouveau compte dans MetaMask ou générez une clé privée.
2.  **Obtenez du MATIC de test** : Allez sur le [Polygon Faucet](https://faucet.polygon.technology/) et entrez l'adresse de ce portefeuille serveur.
3.  Récupérez la **Clé Privée** de ce portefeuille.

## 3. Configuration des Variables d'Environnement

Éditez votre fichier `.env` à la racine du projet :

```env
# URL du nœud Polygon Amoy (utilisez celle par défaut ou une clé Alchemy/Infura)
BLOCKCHAIN_RPC_URL=https://rpc-amoy.polygon.technology

# ID de la chaîne (80002 pour Amoy)
BLOCKCHAIN_CHAIN_ID=80002

# L'adresse obtenue à l'étape 1
CONTRACT_ADDRESS=0xVOTRE_ADRESSE_DE_CONTRAT

# La clé privée obtenue à l'étape 2 (SANS le 0x au début)
BLOCKCHAIN_PRIVATE_KEY=VOTRE_CLE_PRIVEE_SERVEUR
```

## 4. Flux d'utilisation des API (Étape par Étape)

Voici l'ordre exact des appels à faire dans `test_frontend_1.html` pour un cycle complet :

### Étape A : Émission (Issue)
- **Endpoint** : `POST /api/diplomas/issue/`
- **Action** : Remplit les infos de l'étudiant.
- **Résultat** : Le serveur génère le PDF et vous donne un `hash_to_sign`.

### Étape B : Signature MetaMask
- **Action** : Cliquez sur "Signer avec MetaMask" dans l'interface.
- **Détail** : MetaMask signe le hash. Cela prouve l'identité de l'université.

### Étape C : Confirmation Signature
- **Endpoint** : `POST /api/diplomas/{id}/confirm-eth-sig/`
- **Action** : Envoie la signature de MetaMask au serveur.
- **Résultat** : Le diplôme passe au statut `signed`.

### Étape D : Ancrage Blockchain (C'est ici que la transaction part)
- **Endpoint** : `POST /api/diplomas/{id}/anchor/`
- **Action** : Cliquez sur le bouton dans la vue "Anchor".
- **Détail** : Le serveur utilise sa `BLOCKCHAIN_PRIVATE_KEY` pour envoyer le hash au `CONTRACT_ADDRESS`.
- **Résultat** : Vous recevez un `tx_hash`. Le diplôme est désormais immuable sur Polygon.

## 5. Vérification

Une fois ancré, si vous allez dans **Verification par upload**, le système affichera :
- `blockchain_anchored: true` (il le voit en base de données)
- `blockchain_verified_realtime: true` (il a interrogé le smart contract en direct et a trouvé le hash)

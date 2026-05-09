// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @dev Importation directe via GitHub pour une compatibilité immédiate avec Remix IDE
 */
import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/utils/cryptography/ECDSA.sol";
import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/utils/cryptography/MessageHashUtils.sol";

/**
 * @title DiplomaRegistry
 * @dev Registre immuable pour l'ancrage des hashs de diplômes.
 * Sécurisé contre les attaques de phishing et vérifie les signatures on-chain.
 */
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

    /**
     * @dev Ancre un diplôme en vérifiant la signature de l'université.
     * @param _fileHash Le hash SHA-256 du PDF.
     * @param _signature La signature produite par MetaMask (personal_sign).
     * @param _university L'adresse de l'université qui a signé.
     */
    function anchorDiploma(
        bytes32 _fileHash, 
        bytes calldata _signature, 
        address _university
    ) public {
        require(!diplomas[_fileHash].exists, "Diplome deja ancre");
        
        // Reconstruction du hash du message signé par MetaMask (prefixé \x19Ethereum...)
        bytes32 signedMessageHash = _fileHash.toEthSignedMessageHash();
        
        // Récupération de l'adresse du signataire
        address signer = signedMessageHash.recover(_signature);
        
        require(signer == _university, "Signature invalide ou mauvais signataire");

        diplomas[_fileHash] = Diploma(_fileHash, _university, block.timestamp, true);
        
        emit DiplomaAnchored(_fileHash, _university, block.timestamp);
    }
    
    /**
     * @dev Vérifie l'existence d'un diplôme par son hash.
     */
    function verifyDiploma(bytes32 _fileHash) public view returns (bool, address, uint256) {
        Diploma memory d = diplomas[_fileHash];
        return (d.exists, d.university, d.timestamp);
    }
}













































// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";

/// @title DiploChain — Registre de hash de diplômes
/// @notice Ancre les empreintes SHA-256 des diplômes sur Polygon
contract DiploChain is Ownable {

    // Structure d'un diplôme ancré
    struct DiplomaRecord {
        string  diplomaId;          // UUID Django
        string  fileHash;           // SHA-256 hex du PDF
        address universityAddress;  // Wallet MetaMask de l'université
        uint256 timestamp;          // Horodatage automatique
        bool    exists;
    }

    // fileHash => DiplomaRecord
    mapping(string => DiplomaRecord) private records;

    // fileHash => address (université propriétaire)
    mapping(string => address) private owners;

    // Événements
    event DiplomaAnchored(
        string indexed fileHash,
        string  diplomaId,
        address indexed universityAddress,
        uint256 timestamp
    );

    event DiplomaRevoked(
        string indexed fileHash,
        address indexed revokedBy,
        uint256 timestamp
    );

    /// @notice Ancre le hash d'un diplôme sur la blockchain
    /// @dev Seule une université autorisée peut ancrer
    /// @param fileHash   Hash SHA-256 hex du PDF (64 chars)
    /// @param diplomaId  UUID du diplôme dans Django
    function anchorDiploma(
        string calldata fileHash,
        string calldata diplomaId
    ) external onlyOwner {
        require(bytes(fileHash).length == 64, "Hash invalide: 64 chars requis");
        require(!records[fileHash].exists, "Hash deja ancre

        records[fileHash] = DiplomaRecord({
            diplomaId:         diplomaId,
            fileHash:          fileHash,
            universityAddress: msg.sender,
            timestamp:         block.timestamp,
            exists:            true
        });
        owners[fileHash] = msg.sender;

        emit DiplomaAnchored(fileHash, diplomaId, msg.sender, block.timestamp);
    }

    /// @notice Vérifie si un hash est ancré et retourne ses données
    function verifyDiploma(string calldata fileHash)
        external view
        returns (bool found, string memory diplomaId,
                 address universityAddress, uint256 timestamp)
    {
        DiplomaRecord memory r = records[fileHash];
        return (r.exists, r.diplomaId, r.universityAddress, r.timestamp);
    }

    /// @notice Révoque un diplôme (seul l'émetteur peut le faire)
    function revokeDiploma(string calldata fileHash) external {
        require(records[fileHash].exists, "Hash non trouvé");
        require(owners[fileHash] == msg.sender, "Non autorisé");
        delete records[fileHash];
        emit DiplomaRevoked(fileHash, msg.sender, block.timestamp);
    }
}
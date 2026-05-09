"""
diplomas/blockchain_service.py

Service pour interagir avec la blockchain Polygon (Amoy Testnet).
Permet d'ancrer le hash d'un diplôme dans un smart contract.
"""

import json
import logging
from django.conf import settings
from web3 import Web3

logger = logging.getLogger(__name__)

# ABI minimal pour le contrat DiplomaRegistry
# On suppose un contrat avec une fonction : anchorDiploma(bytes32 fileHash)
DIPLOMA_REGISTRY_ABI = [
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"internalType": "bytes32",
				"name": "fileHash",
				"type": "bytes32"
			},
			{
				"indexed": True,
				"internalType": "address",
				"name": "university",
				"type": "address"
			},
			{
				"indexed": False,
				"internalType": "uint256",
				"name": "timestamp",
				"type": "uint256"
			}
		],
		"name": "DiplomaAnchored",
		"type": "event"
	},
	{
		"inputs": [
			{
				"internalType": "bytes32",
				"name": "_fileHash",
				"type": "bytes32"
			},
			{
				"internalType": "bytes",
				"name": "_signature",
				"type": "bytes"
			},
			{
				"internalType": "address",
				"name": "_university",
				"type": "address"
			}
		],
		"name": "anchorDiploma",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
    # ... (view functions stay the same)
]

class PolygonService:
    # ... (__init__ and is_connected stay the same)

    def anchor_diploma(self, file_hash_hex: str, eth_signature: str, university_address: str):
        """
        Envoie une transaction on-chain sécurisée.
        
        Args:
            file_hash_hex: Le hash SHA-256 du PDF
            eth_signature: La signature produite par MetaMask (0x...)
            university_address: L'adresse de l'université
        """
        if not self.contract or not self.account:
            logger.error("Blockchain service non configuré.")
            return None, None

        try:
            if not file_hash_hex.startswith("0x"):
                file_hash_hex = "0x" + file_hash_hex
            file_hash_bytes = self.w3.to_bytes(hexstr=file_hash_hex)
            
            # Signature et adresse
            sig_bytes = self.w3.to_bytes(hexstr=eth_signature)
            univ_addr = self.w3.to_checksum_address(university_address)

            # Préparer la transaction
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            func = self.contract.functions.anchorDiploma(
                file_hash_bytes, 
                sig_bytes, 
                univ_addr
            )
            
            gas_estimate = func.estimate_gas({'from': self.account.address})

            tx = func.build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': int(gas_estimate * 1.2),
                'gasPrice': self.w3.eth.gas_price,
                'chainId': settings.BLOCKCHAIN_CHAIN_ID
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt['status'] == 1:
                return tx_hash.hex(), receipt['blockNumber']
            return None, None

        except Exception as e:
            logger.exception(f"Erreur ancrage : {str(e)}")
            return None, None

    def verify_on_chain(self, file_hash_hex: str):
        """
        Vérifie si un hash est déjà présent dans le smart contract.
        """
        if not self.contract:
            return False
            
        try:
            if not file_hash_hex.startswith("0x"):
                file_hash_hex = "0x" + file_hash_hex
            file_hash_bytes = self.w3.to_bytes(hexstr=file_hash_hex)
            
            result = self.contract.functions.diplomas(file_hash_bytes).call()
            return result[3] # Le booléen 'exists' dans le struct
        except Exception as e:
            logger.error(f"Erreur vérification on-chain : {e}")
            return False

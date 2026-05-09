import os
import django
from web3 import Web3
from django.conf import settings

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_blockchain_connection():
    print("--- Test de Connexion Blockchain ---")
    
    # 1. Vérification du RPC Alchemy
    w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_RPC_URL))
    if w3.is_connected():
        print(f"[OK] Connecté au RPC : {settings.BLOCKCHAIN_RPC_URL}")
    else:
        print(f"[ERREUR] Impossible de se connecter au RPC. Vérifiez votre URL Alchemy.")
        return

    # 2. Vérification du Réseau (Chain ID)
    chain_id = w3.eth.chain_id
    if chain_id == settings.BLOCKCHAIN_CHAIN_ID:
        print(f"[OK] Réseau correct : Chain ID {chain_id} (Amoy)")
    else:
        print(f"[ERREUR] Mauvais réseau. Attendu: {settings.BLOCKCHAIN_CHAIN_ID}, Reçu: {chain_id}")

    # 3. Vérification du Contrat
    try:
        contract_address = w3.to_checksum_address(settings.CONTRACT_ADDRESS)
        code = w3.eth.get_code(contract_address)
        if code != w3.to_bytes(hexstr="0x"):
            print(f"[OK] Contrat trouvé à l'adresse : {contract_address}")
        else:
            print(f"[ERREUR] Aucun contrat trouvé à l'adresse {contract_address}. Vérifiez CONTRACT_ADDRESS.")
    except Exception as e:
        print(f"[ERREUR] Adresse invalide ou problème de contrat : {e}")

    # 4. Vérification du Compte (Gas Station)
    try:
        from eth_account import Account
        account = Account.from_key(settings.BLOCKCHAIN_PRIVATE_KEY)
        balance_wei = w3.eth.get_balance(account.address)
        balance_pol = w3.from_wei(balance_wei, 'ether')
        print(f"[OK] Compte Serveur : {account.address}")
        print(f"[INFO] Solde : {balance_pol} POL")
        
        if balance_pol < 0.01:
            print("[ATTENTION] Solde faible. Vous risquez de manquer de gaz pour l'ancrage.")
    except Exception as e:
        print(f"[ERREUR] Problème avec BLOCKCHAIN_PRIVATE_KEY : {e}")

if __name__ == "__main__":
    test_blockchain_connection()

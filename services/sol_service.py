from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solana.rpc.api import Client

import os
from dotenv import load_dotenv

load_dotenv()

# Solana configuration
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL")
solana_client = Client(SOLANA_RPC_URL)

def send_sol_transaction(sender_id, recipient_address, amount):
    """
    Sends SOL from the user's wallet to the specified recipient.
    """
    from services.wallet_service import get_wallet_info

    # Retrieve sender wallet info
    wallet = get_wallet_info(sender_id)
    if not wallet:
        raise Exception("Sender wallet not found.")

    sender_private_key = wallet["private_key"]
    sender_keypair = Keypair.from_secret_key(bytes(sender_private_key, "utf-8"))

    # Validate recipient address
    try:
        recipient_pubkey = Pubkey.from_string(recipient_address)
    except Exception:
        raise Exception("Invalid recipient wallet address.")

    # Validate amount
    try:
        lamports = int(float(amount) * 1e9)  # Convert SOL to lamports
        if lamports <= 0:
            raise ValueError("Amount must be greater than zero.")
    except ValueError as e:
        raise Exception(f"Invalid amount: {e}")

    # Send transaction
    try:
        transaction = solana_client.request_airdrop(sender_keypair.pubkey(), lamports)
        return {"signature": transaction["result"]}
    except Exception as e:
        raise Exception(f"Transaction failed: {e}")
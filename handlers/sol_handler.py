from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.message import Message
from solders.system_program import transfer, TransferParams
from solana.rpc.api import Client
import base64


# Solana RPC client
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"  # Replace with "https://api.devnet.solana.com" for testing

def send_sol_transaction(sender_wallet, sender_private_key, recipient_wallet, amount):
    """
    Sends SOL from the sender's wallet to the recipient's wallet using `solders`.

    Args:
        sender_wallet (str): The sender's public wallet address (base58-encoded string).
        sender_private_key (str): The sender's private key in base64 format.
        recipient_wallet (str): The recipient's public wallet address (base58-encoded string).
        amount (float): The amount of SOL to send.

    Returns:
        dict: A dictionary with the status of the transaction.
    """
    try:
        rpc_client = Client(SOLANA_RPC_URL)
        # Validate recipient wallet address
        if not recipient_wallet or len(recipient_wallet) != 44:
            return {"success": False, "error": "Invalid recipient wallet address."}

        # Convert public key strings to `Pubkey` objects
        sender_pubkey = Pubkey.from_string(sender_wallet)
        recipient_pubkey = Pubkey.from_string(recipient_wallet)

        # Decode the sender's private key from base64
        try:
            sender_private_key_bytes = base64.b64decode(sender_private_key)
            sender_public_key_bytes = bytes(Pubkey.from_string(sender_wallet))
            # Combine the 32-byte secret key with the 32-byte public key to form the full 64-byte private key
            full_private_key = sender_private_key_bytes + sender_public_key_bytes
    
            sender_keypair = Keypair.from_bytes(full_private_key)
        except Exception as e:
            return {"success": False, "error": f"Invalid private key: {str(e)}"}


        # check sender balance & validate
        sender_balance = rpc_client.get_balance(sender_pubkey).value
        lamports = int(amount * 1e9)


        ixns = [transfer(TransferParams(from_pubkey=sender_pubkey, to_pubkey=recipient_pubkey, lamports=lamports))]
        msg = Message(ixns, sender_pubkey)

        fees = rpc_client.get_fee_for_message(msg).value or 0

        if sender_balance < lamports + fees:
            return {"success": False, "error": "Insufficient balance."}

        for i in range(5):
            try:
                # latest_blockhash = rpc_client.get_latest_blockhash().value.blockhash
                transaction = Transaction([sender_keypair], msg, rpc_client.get_latest_blockhash().value.blockhash)
                response = rpc_client.send_transaction(transaction)
                break
            except Exception as e:
                if i == 4:
                    return {"success": False, "error": f"Failed to send transaction: {str(e)}"}
        
        # Extract the transaction signature
        signature = response.value
        if not signature:
            return {"success": False, "error": "Transaction failed. No signature received."}


        # SEND FEES TO PROJECT WALLET

        # Confirm the transaction
        # confirmation = rpc_client.get_signature_statuses([signature]).value
        # print(confirmation, '***')
        # if not confirmation or not confirmation[0]:
        #     return {"success": False, "error": "Transaction confirmation failed."}




        return {
            "success": True,
            "transaction_signature": signature,
            "message": f"Successfully sent {amount} SOL from {sender_wallet} to {recipient_wallet}."
        }

    except Exception as e:
        return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}
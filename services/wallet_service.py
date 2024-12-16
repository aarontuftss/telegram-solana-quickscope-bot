import datetime
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
import base64
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"  # Replace with "https://api.devnet.solana.com" for testing
rpc_client = Client(SOLANA_RPC_URL)

def create_wallet(user_id):
    """
    Creates a wallet for the user if it doesn't exist.
    """
    result = supabase.table("Wallets").select("public_key").eq("user_id", user_id).execute()
    if result.data:
        return None  # Wallet already exists

    # Create new wallet
    keypair = Keypair()
    public_key = str(keypair.pubkey())
    # private_key = keypair.secret().decode()
    private_key = base64.b64encode(bytes(keypair.secret())).decode()  # Encode private key in Base64


    supabase.table("Wallets").insert({
        "user_id": user_id,
        "public_key": public_key,
        "private_key": private_key
    }).execute()

    return {"public_key": public_key}

def get_wallet_info(user_id):
    """
    Retrieves wallet info and balance from the database and Solana blockchain.
    """

    # Fetch the wallet details from the database
    result = supabase.table("Wallets").select("public_key").eq("user_id", user_id).execute()
    if not result.data:
        return None

    # Extract the public key
    public_key_str = result.data[0]["public_key"]
    public_key = Pubkey.from_string(public_key_str)

    # Fetch the wallet balance from Solana blockchain
    response = rpc_client.get_balance(public_key)
    balance_lamports = response.value
    balance_sol = balance_lamports / 1e9  # Convert lamports to SOL

    # Return wallet information and balance
    return {"public_key": public_key, "balance": balance_sol}


def generate_qr_code(data):
    """
    Generates a QR code for the given data.
    """
    import qrcode
    import io

    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill="black", back_color="white")
    output = io.BytesIO()
    img.save(output, "PNG")
    output.seek(0)
    return output



def get_wallet_public_key(user_id):
    """Fetch the public key for a user's wallet from Supabase."""
    result = supabase.table("Wallets").select("public_key").eq("user_id", user_id).execute()
    if result.data:
        return result.data[0]["public_key"]
    return None

# def fetch_trades(public_key, offset, limit):
#     """Fetch a paginated list of transactions for the wallet."""
#     # Placeholder implementation
#     # Replace with Solana API or relevant data source for fetching transactions
#     transactions = [
#         {"tx_id": f"Tx{offset + i + 1}", "amount": 1.23, "date": "2024-12-16"}
#         for i in range(limit)
#     ]
#     total_count = 50  # Replace with actual count from the data source
#     return transactions, total_count

def fetch_trades(public_key, offset, limit):
    """
    Fetch a paginated list of transactions for the wallet.

    Args:
        public_key (str): The public key of the wallet.
        offset (int): The starting index for pagination.
        limit (int): The number of transactions to fetch.

    Returns:
        list, int: A list of transactions and the total count of transactions.
    """
    try:
        # Convert public key string to Pubkey object
        wallet_pubkey = Pubkey.from_string(public_key)
        
        # Fetch signatures for the wallet address
        response = rpc_client.get_signatures_for_address(wallet_pubkey, limit=1000)
        if not response or not response.value:
            return [], 0  # No transactions found

        # Extract and paginate transactions
        all_signatures = response.value  # List of transaction signatures
        total_count = len(all_signatures)
        paginated_signatures = all_signatures[offset:offset + limit]

        transactions = []
        for signature_data in paginated_signatures:
            # Get transaction details
            tx_signature = signature_data['signature']
            tx_response = rpc_client.get_transaction(tx_signature)
            if not tx_response or not tx_response.value:
                continue

            # Extract relevant transaction data
            tx = tx_response.value['transaction']
            meta = tx_response.value['meta']
            
            # Get the amount of SOL transferred in the transaction
            pre_balances = meta.get('preBalances', [])
            post_balances = meta.get('postBalances', [])
            sol_diff = (pre_balances[0] - post_balances[0]) / 1e9  # Convert lamports to SOL

            # Get transaction date (block time)
            block_time = tx_response.value.get('blockTime')
            date = datetime.utcfromtimestamp(block_time).strftime('%Y-%m-%d %H:%M:%S') if block_time else "Unknown"

            # Append transaction details
            transactions.append({
                "tx_id": tx_signature,
                "amount": sol_diff,
                "date": date
            })
        print(transactions)
        print(total_count)
        return transactions, total_count

    except Exception as e:
        print(f"Error fetching transactions: {e}")
        return [], 0
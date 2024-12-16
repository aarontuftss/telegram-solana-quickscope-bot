import asyncio
import datetime
import httpx
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
import base64
import os
from dotenv import load_dotenv
from supabase import create_client
from dotenv import load_dotenv
from cachetools import TTLCache

from services.user_config_service import create_user_config

# Define the TTL cache (maxsize=100, ttl=3600 seconds = 1 hour)
cache = TTLCache(maxsize=100, ttl=3600)

load_dotenv()

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")  # Store your Helius API key in an environment variable
HELIUS_API_URL = "https://api.helius.xyz/v0/addresses/{address}/transactions/"



load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"  # Replace with "https://api.devnet.solana.com" for testing

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
    rpc_client = Client(SOLANA_RPC_URL)


    # Fetch the wallet details from the database
    result = supabase.table("Wallets").select("public_key").eq("user_id", user_id).execute()
    if not result.data:
        result = create_wallet(user_id)
        create_user_config(user_id)

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
    
async def fetch_trades(public_key, offset, limit):
    try:

        # Generate a unique cache key
        cache_key = f"{public_key}-{offset}-{limit}"
        
        # Check if the result is already cached
        if cache_key in cache:
            return cache[cache_key]

        url = HELIUS_API_URL.format(address=public_key)
        params = {"api-key": HELIUS_API_KEY}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            if response.status_code != 200:
                raise Exception(f"Helius API returned {response.status_code}: {response.text}")

            # Parse the response
            data = response.json()
            total_count = len(data)
            paginated_data = data[offset:offset + limit]

            transactions = []
            for tx in paginated_data:
                timestamp = tx.get("timestamp")
                fee = tx.get("fee", 0) / 1e9  # Convert lamports to SOL
                date = (
                    datetime.datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    if timestamp
                    else "Unknown"
                )

                # Process native transfers
                native_transfers = [
                    {
                        "from": transfer.get("fromUserAccount", "Unknown"),
                        "to": transfer.get("toUserAccount", "Unknown"),
                        "amount": transfer.get("amount", 0) / 1e9  # Convert lamports to SOL
                    }
                    for transfer in tx.get("nativeTransfers", [])
                ]

                # Process token transfers
                token_transfers = [
                    {
                        "token": transfer.get("mint", "Unknown"),
                        "from": transfer.get("fromUserAccount", "Unknown"),
                        "to": transfer.get("toUserAccount", "Unknown"),
                        "amount": transfer.get("tokenAmount", {}).get("amount", 0) /
                                (10 ** transfer.get("tokenAmount", {}).get("decimals", 0))
                    }
                    for transfer in tx.get("tokenTransfers", [])
                ]

                # Only include native transfers or token transfers, not both
                transactions.append({
                    "date": date,
                    "fee": f"{fee:.9f}",
                    "native_transfers": native_transfers if native_transfers else None,
                    "token_transfers": token_transfers if not native_transfers and token_transfers else None,
                })
            cache[cache_key] = (transactions, total_count)
            return transactions, total_count

    except Exception as e:
        print(f"Error fetching transactions from Helius: {e}")
        return [], 0
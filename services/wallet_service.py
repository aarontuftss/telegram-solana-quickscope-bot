import asyncio
import datetime
import httpx
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solana.rpc.types import TokenAccountOpts
import base64
import os
from dotenv import load_dotenv
from supabase import create_client
from dotenv import load_dotenv
from cachetools import TTLCache

import requests

from services.user_config_service import create_user_config

# Define the TTL cache (maxsize=100, ttl=3600 seconds = 1 hour)
cache = TTLCache(maxsize=100, ttl=900)

load_dotenv()

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")  # Store your Helius API key in an environment variable
HELIUS_API_URL = "https://api.helius.xyz/v0/addresses/{address}/transactions/"

SOLANA_FM_TRANSACTIONS_URL = "https://api.solana.fm/v0/accounts/{address}/transfers"
SOLANA_FM_BALANCE_URL = "https://api.solana.fm/v1/tokens/{address}/token-accounts"


SOL_TRACKER_API_URL = "https://data.solanatracker.io/wallet/{address}"



load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
SOL_TRACKER_KEY = os.getenv("SOL_TRACKER_KEY")



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

    # Fetch the wallet details from the database
    result = supabase.table("Wallets").select("public_key").eq("user_id", user_id).execute()
    if not result.data:
        result = create_wallet(user_id)
        create_user_config(user_id)

    # Extract the public key
    public_key_str = result.data[0]["public_key"]
    public_key = Pubkey.from_string(public_key_str)

    url = SOLANA_FM_BALANCE_URL.format(address=public_key)
    response = requests.post(url, json={ "includeSolBalance": True })
    response_json = response.json()
    balance_sol = response_json['solBalance']
    filtered_token_accounts = [token for token in response_json['tokenAccounts'] if token['info']['tokenAmount']['uiAmount'] > 0]
    num_coins = len(filtered_token_accounts)

    return {"public_key": public_key, "balance": balance_sol, "num_coins": num_coins}


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

async def fetch_trades(public_key, page=1, limit=10):
    """
    Fetch trades for a public key using SolanaTracker API.

    Args:
        public_key (str): The public key to fetch transactions for.
        page (int): The page number for pagination.
        limit (int): The number of items to fetch per page.

    Returns:
        dict: A dictionary containing paginated trade data and total pages.
    """
    try:
        # Construct the API request URL
        url = SOL_TRACKER_API_URL.format(address=public_key)

        # Make the request to SolanaTracker API
        response = requests.get(url, headers={"x-api-key": SOL_TRACKER_KEY})
        if response.status_code != 200:
            raise Exception(f"SolanaTracker API returned {response.status_code}: {response.text}")

        # Parse the response
        data = response.json()

        # Format the data for display
        formatted_trades = [
            {
                "name": token["token"]["name"],
                "symbol": token["token"]["symbol"],
                "balance": f"{token['balance']:.9f} {token['token']['symbol']}",
                "usd_value": f"${token['value']:.2f}",
                "image": token["token"]["image"],
                'mint_address': token['token']['mint'],
            }
            for token in data['tokens']
        ]

        return formatted_trades

    except Exception as e:
        print(f"Error fetching trades from SolanaTracker: {e}")
        return {"trades": [], "total_pages": 0}
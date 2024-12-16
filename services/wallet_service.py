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

import requests

from services.user_config_service import create_user_config

# Define the TTL cache (maxsize=100, ttl=3600 seconds = 1 hour)
cache = TTLCache(maxsize=100, ttl=900)

load_dotenv()

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")  # Store your Helius API key in an environment variable
HELIUS_API_URL = "https://api.helius.xyz/v0/addresses/{address}/transactions/"

SOLANA_FM_TRANSACTIONS_URL = "https://api.solana.fm/v0/accounts/{address}/transfers"



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

async def fetch_trades(public_key, page=1, limit=10):
    """
    Fetch trades for a public key using Solana.fm API.

    Args:
        public_key (str): The public key to fetch transactions for.
        page (int): The page number for pagination.
        limit (int): The number of transactions to fetch per page.

    Returns:
        tuple: A tuple containing the transactions and the total count.
    """
    try:
        # # Generate a unique cache key
        cache_key = f"{public_key}-page-{page}-limit-{limit}"
        
        # # Check if the result is already cached
        if cache_key in cache:
            return cache[cache_key]

        # Construct the API request URL
        url = SOLANA_FM_TRANSACTIONS_URL.format(address=public_key)

        # Set up request parameters for pagination
        params = {"page": page, "limit": limit}

        # Make the request to Solana.fm API
        response = requests.get(url, params=params)
        # Check for a successful response
        if response.status_code != 200:
            raise Exception(f"Solana.fm API returned {response.status_code}: {response.text}")

        # Parse the response
        data = response.json()
        total_pages = data['pagination']['totalPages']
        transactions_data = data['results']
        transactions = []
        for tx in transactions_data:
            fee_object = tx['data'][0]
            payment_object = tx['data'][1]
            if not fee_object or not payment_object:
                continue
            timestamp = payment_object.get("timestamp")
            fee = fee_object.get("amount", 0) / 1e9  # Convert lamports to SOL
            date = (
                datetime.datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                if timestamp
                else "Unknown"
            )

            transfer_obj = {
                "from": payment_object.get("source", "Unknown"),
                "to": payment_object.get("destination", "Unknown"),
                "amount": payment_object.get("amount", 0) / 1e9,  # Convert lamports to SOL
                'token': payment_object.get("token", "SOL")
            }

            # Only include native transfers or token transfers, not both
            transactions.append({
                "date": date,
                "fee": f"{fee:.9f}",
                'transfer_obj': transfer_obj
            })

        # Cache the result
        cache[cache_key] = (transactions, total_pages)
        return transactions, total_pages

    except Exception as e:
        print(f"Error fetching transactions from Solana.fm: {e}")
        return [], 0


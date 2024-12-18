import base64
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solanatracker import SolanaTracker
from services.user_config_service import fetch_user_config
import requests
from dotenv import load_dotenv
import os
from supabase import create_client, Client as SupabaseClient


JUPITER_API_URL = "https://quote-api.jup.ag/v6"

# Load environment variables
load_dotenv()

SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL")
SOL_TRACKER_KEY = os.getenv("SOL_TRACKER_KEY")
client = Client(SOLANA_RPC_URL)

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: SupabaseClient = create_client(supabase_url, supabase_key)

SOL_MINT_ADDRESS = "So11111111111111111111111111111111111111112"

def get_published_solana_coin_info(mint_address):
    try:
        # Fetch token price using Jupiter API
        price_data = requests.get(f'https://data.solanatracker.io/tokens/{mint_address}', headers={'x-api-key': SOL_TRACKER_KEY})
        price_data = price_data.json()


        return {
            "name": price_data['token']['name'],
            "symbol": price_data['token']['symbol'],
            "description": price_data['token']['description'],
            "image_url": price_data['token']['image'],
            "mint_address": mint_address,
            "price": price_data['pools'][0]['price']['usd'],
            "price_change_5m": price_data['events']['5m']['priceChangePercentage'],
            "price_change_1h": price_data['events']['1h']['priceChangePercentage'],
            "price_change_6h": price_data['events']['6h']['priceChangePercentage'],
            "price_change_24h": price_data['events']['24h']['priceChangePercentage'],
            "market_cap": price_data['pools'][0]['marketCap']['usd'],
        }

    except Exception as e:
        return {"error": f"Error fetching contract information: {str(e)}"}


def format_number(value, allow_commas=False):
    """
    Formats a number:
      - Rounds to 2 decimal places.
      - Uses scientific notation for very small or very large numbers.
      - Optionally adds commas for large numbers.
    """
    try:
        if value is None or value == 0:
            return "0.00"

        if abs(value) < 0.01 or abs(value) > 1_000_000:  # Use scientific notation for very small or large numbers
            return f"{value:.2e}"

        if allow_commas:
            return f"{value:,.2f}"  # Format with commas and 2 decimals

        return f"{value:.2f}"  # Round to 2 decimal places
    except (ValueError, TypeError):
        return "N/A"
    

async def swap_coin_func(update, context, amount, coin_info, is_sell):
    user_id = update.effective_user.id
    config = fetch_user_config(user_id)

    # IF BUY - CHECK WALLET BALANCE

    # Fetch user's wallet
    user_wallet_response = supabase.table('Wallets').select("*").eq('user_id', user_id).execute()
    if not user_wallet_response.data:
        return {'error': "No wallet found for the user."}

    user_wallet = user_wallet_response.data[0]
    sender_wallet = user_wallet['public_key']
    sender_private_key = user_wallet['private_key']

    if not sender_private_key:
        return {'error': "Private key not set. Unable to proceed."}
    

    sender_private_key_bytes = base64.b64decode(sender_private_key)
    sender_public_key_bytes = bytes(Pubkey.from_string(sender_wallet))
    # Combine the 32-byte secret key with the 32-byte public key to form the full 64-byte private key
    full_private_key = sender_private_key_bytes + sender_public_key_bytes
    sender_keypair = Keypair.from_bytes(full_private_key)
    solana_tracker = SolanaTracker(sender_keypair, "https://rpc.solanatracker.io/public?advancedTx=true") # Your RPC Here
    priority = config['transaction_priority']
    priority_fee = config[f"tp_{priority}"]

    slippage = config['slippage_sell'] if is_sell else config['slippage_buy']
    final_amount = f"{amount * 100}%" if is_sell else amount
    from_token = coin_info['mint_address'] if is_sell else SOL_MINT_ADDRESS
    to_token = SOL_MINT_ADDRESS if is_sell else coin_info['mint_address']

    try:
        swap_response = await solana_tracker.get_swap_instructions(
            from_token,  # From Token
            to_token,  # To Token
            final_amount,  # Amount to swap
            slippage * 100,  # Slippage
            str(sender_keypair.pubkey()),  # Payer public key
            priority_fee,  # Priority fee (Recommended while network is congested)
            True,  # Force legacy transaction for Jupiter
        )

        # Define custom options
        custom_options = {
            "send_options": {"skip_preflight": True, "max_retries": 5},
            "confirmation_retries": 50,
            "confirmation_retry_timeout": 1000,
            "last_valid_block_height_buffer": 200,
            "commitment": "processed",
            "resend_interval": 1500,
            "confirmation_check_interval": 100,
            "skip_confirmation_check": False,
        }

        txid = await solana_tracker.perform_swap(swap_response, options=custom_options)

        return {
            'message': f"Transaction successful! Check your transaction here: "
                        f"[solscan.io](https://solscan.io/tx/{txid})"
        }

    except Exception as e:
        return {'error': f"Error occurred: {str(e)}"}
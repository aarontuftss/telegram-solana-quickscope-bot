from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ForceReply
from telegram.ext import ContextTypes
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from handlers.utils import getRespFunc
from services.user_config_service import fetch_user_config
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL")

SOL_TRACKER_KEY = os.getenv("SOL_TRACKER_KEY")

client = Client(SOLANA_RPC_URL)

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

def get_pump_fun_coin_info(mint_address):
    # get pump fun info
    return {}


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
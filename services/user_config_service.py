from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def create_user_config(user_id):
    """
    Creates a User-Config row with default values for the given user_id.
    """
    # Check if the User-Config row already exists
    result = supabase.table("User-Config").select("*").eq("user_id", user_id).execute()

    if result.data:
        return None  # User-Config already exists

    # Insert default User-Config row
    default_config = {
        "user_id": user_id,
        'buy_left': 1.0,
        'buy_right': 5.0,
        'sell_left': 0.25,
        'sell_right': 1.0,
        'sell_initial': True,
        'slippage_buy': 0.1,
        'slippage_sell': 1.0,
        'max_price_impact': 0.25,
        'mev_protect': True,
        'transaction_priority': 'medium',
        'tp_medium': 0.00100,
        'tp_high': 0.00500,
        'tp_very_high': 0.01000,
    }
    supabase.table("User-Config").insert(default_config).execute()


def fetch_user_config(user_id):
    """
    Fetch the User-Config row for the given user_id.
    """
    result = supabase.table("User-Config").select("*").eq("user_id", user_id).execute()
    if result.data:
        return result.data[0]
    else:
        create_user_config(user_id)
        return fetch_user_config(user_id)

def update_user_config(user_id, updates):
    """
    Updates the User-Config row for the given user_id with new values.
    """
    supabase.table("User-Config").update(updates).eq("user_id", user_id).execute()
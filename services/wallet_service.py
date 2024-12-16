from solders.keypair import Keypair
from supabase import create_client
import base64

import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
    Retrieves wallet info from the database.
    """
    result = supabase.table("Wallets").select("public_key").eq("user_id", user_id).execute()
    if not result.data:
        return None

    public_key = result.data[0]["public_key"]
    # Fetch balance (mocked for simplicity)
    balance = 0.0
    return {"public_key": public_key, "balance": balance}

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
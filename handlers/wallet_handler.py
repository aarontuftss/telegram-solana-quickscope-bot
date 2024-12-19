from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from handlers.utils import getRespFunc
from services.wallet_service import fetch_trades, get_wallet_info, generate_qr_code, get_wallet_public_key

from math import ceil


PAGE_SIZE = 5  # Number of transactions per page

async def trades(update, context):
    user_id = update.effective_user.id
    func = getRespFunc(update)
    loading_message = await func("🔄 Loading your wallet, please wait...")

    # Get user's wallet public key
    public_key = get_wallet_public_key(user_id)
    if not public_key:
        await func("No wallet found for this user.")
        return

    # Fetch the first page of transactions
    coins = await fetch_trades(public_key, 1, PAGE_SIZE)
    if not coins:
        await func("No transactions found for this wallet.")
        return

    message = (
        "📈 Your Coins\n"
        "---------------------------------------\n\n"
    )

    for coin in coins:
        message += (
            f"Name: {coin['name']}\n"
            f"Symbol: {coin['symbol']}\n"
            f"Balance: {coin['balance']}\n"
            f"USD Value: {coin['usd_value']}\n\n"
            f"Mint Address: `{coin['mint_address']}` (tap to copy)\n\n"
            "---------------------------------------\n\n"
        )

    await loading_message.edit_text(message, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Close", callback_data="close")]]), parse_mode="Markdown")
    return

async def trades_callback_handler(update, context):
    """Handle pagination and message deletion for trades."""
    func = getRespFunc(update)
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("trades_page_"):
        return
    elif data == "trades_delete_message":
        await query.message.delete()

async def wallet_info(update: Update, context):
    """
    Fetch and display the wallet information.
    """
    user_id = update.effective_user.id
    wallet = get_wallet_info(user_id)

    keyboard = [
        
        [InlineKeyboardButton("Your Coins", callback_data="main_trades")],
        [InlineKeyboardButton("Export Private Keys", callback_data="main_export_keys"), InlineKeyboardButton("Close", callback_data="close")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    
    message = (
        "🔑 Your wallet information\n"
        f"--------------------------------\n\n"
        f"Public Key: `{wallet['public_key']}`\n\n"
        f"Balance: {wallet['balance']} SOL\n\n"
        f"# of Coins {wallet['num_coins']}\n"
        f"--------------------------------\n\n"
    )

    await update.callback_query.message.reply_text(
        message, reply_markup=reply_markup, parse_mode="Markdown"
    )

async def add_funds(update: Update, context):
    """
    Provide funding options: MoonPay or QR code.
    """
    user_id = update.effective_user.id
    wallet = get_wallet_info(user_id)

    public_key = wallet['public_key']
    moonpay_url = f"https://www.moonpay.com/"
    qr_image = generate_qr_code(public_key)

    message = (
        f"Public Key as a QR code ⬆️\n\n"
        f"----------------------------\n\n"
        f"Current balance: {wallet['balance']} SOL\n\n"
        f"\n💰 Add funds to your wallet\n"
        f"----------------------------\n\n"
        f"Public Key: `{public_key}` (tap to copy)\n\n"
        f"Or [Buy with MoonPay]({moonpay_url})\n\n"
    )

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Close", callback_data="close")]])


    await context.bot.send_photo(photo=qr_image, caption=message, parse_mode="Markdown", reply_markup=reply_markup ,chat_id=update.effective_chat.id)
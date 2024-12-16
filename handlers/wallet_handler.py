from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from services.wallet_service import fetch_trades, get_wallet_info, generate_qr_code, get_wallet_public_key

from math import ceil


PAGE_SIZE = 5  # Number of transactions per page

def getRespFunc(update):
    if hasattr(update, 'callback_query') and update.callback_query:
        return update.callback_query.message.reply_text
    elif hasattr(update, 'message') and update.message:
        return update.message.reply_text

async def trades(update, context):
    user_id = update.effective_user.id
    func = getRespFunc(update)
    loading_message = await func("🔄 Loading transactions, please wait...")

    # Get user's wallet public key
    public_key = get_wallet_public_key(user_id)
    if not public_key:
        await func("No wallet found for this user.")
        return

    # Fetch the first page of transactions
    transactions, total_count = await fetch_trades(public_key, 0, PAGE_SIZE)
    if not transactions:
        await func("No transactions found for this wallet.")
        return

    # Display transactions
    total_pages = ceil(total_count / PAGE_SIZE)
    await send_paginated_trades(update, context, transactions, public_key, 0, total_pages, loading_message)

async def send_paginated_trades(update, context, transactions, user_wallet, page, total_pages, loading_message):
    """Send a paginated message displaying trades with color-coded logic."""
    func = getRespFunc(update)

    
    # Start building the message
    message = f"Page {page + 1} of {total_pages}:\n\n"
    
    for tx in transactions:
        # Native Transfers
        if tx.get("native_transfers"):
            transfer = tx["native_transfers"][0]  # Assume one primary transfer per transaction
            amount = float(transfer["amount"])
            color = "🟥" if transfer["from"] == user_wallet else "🟩"  # Red for leaving, green for entering
            amount_display = f"{color} {abs(amount):.9f} SOL"

            message += (
                f"**Date:** {tx['date']}\n"
                f"**From:** `{transfer['from']}`\n"
                f"**To:** `{transfer['to']}`\n"
                f"**Amount:** {amount_display}\n"
                f"**Fee:** {tx['fee']} SOL\n\n"
            )

        # Token Transfers
        elif tx.get("token_transfers"):
            transfer = tx["token_transfers"][0]  # Assume one primary transfer per transaction
            amount = float(transfer["amount"])
            color = "🟥" if transfer["from"] == user_wallet else "🟩"  # Red for selling, green for buying
            amount_display = f"{color} {amount:.9f} {transfer['token']}"

            message += (
                f"**Date:** {tx['date']}\n"
                f"**From:** `{transfer['from']}`\n"
                f"**To:** `{transfer['to']}`\n"
                f"**Amount:** {amount_display}\n"
                f"**Fee:** {tx['fee']} SOL\n\n"
            )

    # Pagination buttons
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"trades_page_{page - 1}"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"trades_page_{page + 1}"))
    buttons.append(InlineKeyboardButton("🗑️ Clear", callback_data="trades_delete_message"))

    reply_markup = InlineKeyboardMarkup([buttons])
    # await func(message, reply_markup=reply_markup, parse_mode="Markdown")
    await loading_message.edit_text(message, reply_markup=reply_markup, parse_mode="Markdown")

async def trades_callback_handler(update, context):
    """Handle pagination and message deletion for trades."""
    func = getRespFunc(update)
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("trades_page_"):
        loading_message = await func("🔄 Loading transactions, please wait...")
        page = int(data.split("_")[-1])

        user_id = query.from_user.id
        public_key = get_wallet_public_key(user_id)
        if not public_key:
            await query.edit_message_text("No wallet found for this user.")
            return

        # Fetch transactions for the requested page
        transactions, total_count = await fetch_trades(public_key, page * PAGE_SIZE, PAGE_SIZE)
        total_pages = ceil(total_count / PAGE_SIZE)

        # Update the message with the new page of transactions
        await send_paginated_trades(query, context, transactions, public_key, page, total_pages, loading_message)
    elif data == "trades_delete_message":
        await query.message.delete()

async def wallet_info(update: Update, context):
    """
    Fetch and display the wallet information.
    """
    user_id = update.effective_user.id
    wallet = get_wallet_info(user_id)

    if not wallet:
        await update.callback_query.message.reply_text("No wallet found. Use /start to create one.")
        return

    await update.callback_query.message.reply_text(
        f"Public Key: `{wallet['public_key']}`\nBalance: {wallet['balance']} SOL",
        parse_mode="Markdown"
    )

async def add_funds(update: Update, context):
    """
    Provide funding options: MoonPay or QR code.
    """
    user_id = update.effective_user.id
    wallet = get_wallet_info(user_id)

    if not wallet:
        await update.callback_query.message.reply_text("No wallet found. Use /start to create one.")
        return

    public_key = wallet['public_key']
    moonpay_url = f"https://www.moonpay.com/buy?walletAddress={public_key}&currencyCode=SOL"
    qr_image = generate_qr_code(public_key)

    await update.callback_query.message.reply_text(
        f"Add funds to your wallet:\n\n"
        f"Public Key: `{public_key}`\n\n"
        f"[Buy with MoonPay]({moonpay_url})",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
    await update.callback_query.message.reply_photo(qr_image)
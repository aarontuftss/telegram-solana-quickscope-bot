from telegram import Update
from services.wallet_service import get_wallet_info, generate_qr_code

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
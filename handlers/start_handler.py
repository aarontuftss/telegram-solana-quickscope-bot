from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from services.wallet_service import create_wallet
from services.user_config_service import create_user_config
from telegram import ForceReply

from handlers.settings_handler import settings
from telegram import BotCommand

def getRespFunc(update):
    if hasattr(update, 'callback_query') and update.callback_query:
        return update.callback_query.message.reply_text
    elif hasattr(update, 'message') and update.message:
        return update.message.reply_text


async def buy_coin(update, context):
    user_id = update.effective_user.id
    func = getRespFunc(update)
    await func("Buy Coin button pressed")

async def trades(update, context):
    user_id = update.effective_user.id
    func = getRespFunc(update)
    await func("Trades button pressed")

async def sell_coin(update, context):
    user_id = update.effective_user.id
    func = getRespFunc(update)
    await func("Sell Coin button pressed")

async def help_command(update, context):
    func = getRespFunc(update)
    await func("Help button pressed")

async def about(update, context):
    func = getRespFunc(update)
    await func("About button pressed")

async def send_sol(update, context):
    context.user_data.clear()
    func = getRespFunc(update)
    context.user_data['send_sol_stage'] = 'wallet_address'
    await func(
        "Please enter the recipient's wallet address:",
        reply_markup=ForceReply(selective=True)
    )

async def start(update, context):
    """
    Handles the /start command and displays the main menu with buttons.
    Creates a wallet and User-Config row if they don't exist.
    """
    context.user_data.clear()
    user_id = update.effective_user.id
    username = update.effective_user.username or "User"

    # Check and create wallet if it doesn't exist
    wallet = create_wallet(user_id)
    message = ''
    default_message = '... some stuff about the bot + header image'
    if wallet:
        create_user_config(user_id)
        message = f"Welcome, {username}! \n Your wallet has been created:\n Public Key: `{wallet['public_key']}` \n"
    else:
        message = f"Welcome back, {username}! \n Your wallet already exists. \n"

    # Display menu buttons
    keyboard = [
         [InlineKeyboardButton("📖 About", callback_data="main_about"),
         InlineKeyboardButton("⚙️ Settings", callback_data="main_settings")],

        [InlineKeyboardButton("💳 Wallet Info", callback_data="main_wallet_info"),
         InlineKeyboardButton("💰 Add Funds", callback_data="main_add_funds")],

        [InlineKeyboardButton("💸 Withdraw / Send", callback_data="main_send_sol"),
         InlineKeyboardButton("↔️ Trades", callback_data="main_trades")],

        [InlineKeyboardButton("🟢 Buy Coin", callback_data="main_buy_coin"), 
         InlineKeyboardButton("🔴 Sell Coin", callback_data="main_sell_coin")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(message + default_message, reply_markup=reply_markup, parse_mode="Markdown")

async def menu_handler(update, context):
    """
    Handles button clicks from the main menu.
    """
    query = update.callback_query
    await query.answer()  # Acknowledge button press

    if query.data == "main_wallet_info":
        from handlers.wallet_handler import wallet_info
        await wallet_info(update, context)

    elif query.data == "main_send_sol":
        await send_sol(update, context)

    elif query.data == "main_add_funds":
        from handlers.wallet_handler import add_funds
        await add_funds(update, context)

    elif query.data == "main_settings":
        await settings(update, context)
    elif query.data == "main_buy_coin":
        await buy_coin(update, context)
    elif query.data == "main_trades":
        await trades(update, context)
    elif query.data == "main_sell_coin":
        await sell_coin(update, context)
    elif query.data == "main_help":
        await help_command(update, context)
    elif query.data == "main_about":
        await about(update, context)
    else:
        print("Invalid button pressed", query.data)
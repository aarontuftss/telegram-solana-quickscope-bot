from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from handlers.about_handler import about
from handlers.utils import getRespFunc
from handlers.wallet_handler import trades
from services.wallet_service import create_wallet, get_wallet_info
from services.user_config_service import create_user_config
from telegram import ForceReply

from handlers.settings_handler import settings
from telegram import BotCommand

async def start_transaction(update, context):
    user_id = update.effective_user.id
    func = getRespFunc(update)
    await func("Paste a contract address or a URL from pump.fun, Birdeye, or DEX Screener to start a transaction ⬇️")

async def alerts(update, context):
    user_id = update.effective_user.id
    func = getRespFunc(update)
    await func("Link to main telegram community")

async def refer(update, context):
    user_id = update.effective_user.id
    func = getRespFunc(update)
    bot_url = "https://t.me/thequickscope_bot" 
    message = f"Thank you for your support 🖤\n\n(tap blow to copy)\n`{bot_url}`"
    await func(message, parse_mode="Markdown")


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

    # Check and create wallet if it doesn't exist
    wallet = get_wallet_info(user_id)
    chat_id = update.effective_chat.id
    message = (
        f"Welcome to the Quickscope Bot! \n"
        f"---------------------------------------------\n\n"
        f"`{wallet['public_key']}` (tap to copy) \n \n"
        f"Balance: {wallet['balance']} SOL \n \nYou own {wallet['num_coins']} coins \n\n"
        f"---------------------------------------------\n"
        f"Paste a contract address or a URL from pump.fun, Birdeye, or DEX Screener to start a transaction.\n"
        )

    # Display menu buttons
    keyboard = [
         [InlineKeyboardButton("About", callback_data="main_about"),
         InlineKeyboardButton("Settings", callback_data="main_settings")],

        [InlineKeyboardButton("Wallet Info", callback_data="main_wallet_info"),
         InlineKeyboardButton("Add Funds", callback_data="main_add_funds")],

        [InlineKeyboardButton("Withdraw / Send", callback_data="main_send_sol"),
         InlineKeyboardButton("Your Coins", callback_data="main_trades")],

        [InlineKeyboardButton("Share", callback_data="main_refer"),
         InlineKeyboardButton("Trending", url='https://gmgn.ai/?chain=sol&tab=trending')],

        [InlineKeyboardButton("Buy Coin", callback_data="main_buy_coin"), 
         InlineKeyboardButton("Sell Coin", callback_data="main_sell_coin")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_photo(
        chat_id=chat_id,
        photo='https://ezzsedfstvphracdawzp.supabase.co/storage/v1/object/public/assets/600x200.webp',
        caption=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
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
        await start_transaction(update, context)
    elif query.data == "main_trades":
        await trades(update, context)
    elif query.data == "main_sell_coin":
        await start_transaction(update, context)
    elif query.data == "main_about":
        await about(update, context)
    elif query.data == "main_alerts":
        await alerts(update, context)
    elif query.data == "main_refer":
        await refer(update, context)
    else:
        print("Invalid button pressed", query.data)
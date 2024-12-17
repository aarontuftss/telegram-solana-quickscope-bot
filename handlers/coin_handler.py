from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ForceReply
from telegram.ext import ContextTypes
from handlers.utils import getRespFunc

# Function to get user-configured preset amounts
def get_user_config_amount(action):
    """Fetch user-configured amounts (stubbed for now)."""
    presets = {
        "buy_left": 1.0,  # Example amount for "Buy Left"
        "buy_right": 2.0,
        "sell_left": 1.5,
        "sell_right": 2.5
    }
    return presets.get(action, 1.0)

# Function to fetch coin information
def fetch_coin_info(user_input):
    """Match user input to a coin ticker, URL, or contract address."""
    if user_input.lower() in ["btc", "eth", "sol"]:
        return {"name": user_input.upper(), "price": "100.00", "description": "Sample coin information."}
    elif "http" in user_input or "t.me" in user_input:
        return {"name": "URL Coin", "price": "50.00", "description": "Fetched from URL."}
    elif len(user_input) == 44:  # Contract address format
        return {"name": "Contract Coin", "price": "75.00", "description": "Matched contract address."}
    return None

# Handle incoming coin information
async def handle_coin_info(update, context):
    user_input = update.message.text
    func = getRespFunc(update)

    coin_info = fetch_coin_info(user_input)
    if coin_info:
        # Store state in context.user_data
        context.user_data['coin'] = coin_info['name']
        context.user_data['action'] = None
        context.user_data['amount'] = None

        # Generate buy/sell buttons
        keyboard = [
            [InlineKeyboardButton(f"Buy {get_user_config_amount('buy_left')} SOL", callback_data="buy_left"),
             InlineKeyboardButton("Buy Custom", callback_data="buy_custom"),
             InlineKeyboardButton(f"Buy {get_user_config_amount('buy_right')} SOL", callback_data="buy_right")],
            [InlineKeyboardButton(f"Sell {get_user_config_amount('sell_left')} SOL", callback_data="sell_left"),
             InlineKeyboardButton("Sell Custom", callback_data="sell_custom"),
             InlineKeyboardButton(f"Sell {get_user_config_amount('sell_right')} SOL", callback_data="sell_right")],
            [InlineKeyboardButton("Close", callback_data="close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = f"🔎 *{coin_info['name']}*\n💰 Price: {coin_info['price']} SOL\nℹ️ {coin_info['description']}"
        await func(message, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await func("❌ Coin not recognized. Please try again.")

# Handle button presses for buy/sell
async def handle_buy_sell(update, context):
    query = update.callback_query
    await query.answer()
    func = getRespFunc(update)
    action = query.data  # e.g., "buy_left", "buy_custom"

    context.user_data['action'] = action

    if action in ["buy_custom", "sell_custom"]:
        # Ask user for custom amount
        await query.message.reply_text(
            "Please enter the amount in SOL:",
            reply_markup=ForceReply(selective=True)
        )
    else:
        # Preset buy/sell amount
        preset_amount = get_user_config_amount(action)
        context.user_data['amount'] = preset_amount
        await func(
            f"Please confirm: {action.replace('_', ' ').title()} {preset_amount} SOL?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Confirm", callback_data="confirm"),
                 InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ])
        )

# Handle custom amount reply
async def capture_amount_reply(update, context):
    user_input = update.message.text
    func = getRespFunc(update)

    # Check if user is expected to provide custom amount
    if context.user_data.get('action') in ["buy_custom", "sell_custom"]:
        try:
            amount = float(user_input)
            context.user_data['amount'] = amount

            action = context.user_data['action']
            await func(
                f"Please confirm: {action.replace('_', ' ').title()} {amount} SOL?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Confirm", callback_data="confirm"),
                     InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
                ])
            )
        except ValueError:
            await func("❌ Invalid input. Please enter a valid number for the amount in SOL.")

# Handle confirmation and cancellation
async def handle_confirmation(update, context):
    query = update.callback_query
    await query.answer()
    await query.message.delete()
    func = getRespFunc(update)
    action = context.user_data.get('action')
    amount = context.user_data.get('amount', 0)

    if query.data == "confirm":
        await func(f"✅ {action.replace('_', ' ').title()} confirmed with {amount} SOL.")
    else:
        await func("❌ Action canceled.")


    # Clear state after completion
    context.user_data.clear()

# Handle close button
async def close(update, context):
    query = update.callback_query
    await query.message.delete()
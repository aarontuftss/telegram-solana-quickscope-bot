from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ForceReply
from telegram.ext import ContextTypes
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from handlers.utils import getRespFunc
from services.coin_service import format_number, get_published_solana_coin_info, get_pump_fun_coin_info
from services.user_config_service import fetch_user_config
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL")

client = Client(SOLANA_RPC_URL)


# Function to fetch coin information
def fetch_coin_info(user_input):
    """Match user input to a url or contract address."""

    # check if URL & parse token address
    if 'dexscreener.com/solana' in user_input:
        user_input = user_input.split("/")[-1]
    elif 'pump.fun/coin' in user_input:
        user_input = user_input.split("/")[-1]
    elif 'birdeye.so/token' in user_input:
        user_input = user_input.split("/")[-1].split("?")[0]

    # Check if the input is a 44-character contract address
    if len(user_input) == 44:
        return get_published_solana_coin_info(user_input)

    # Default fallback
    return {"error": "Invalid input. Please provide a valid contract address."}


# Handle incoming coin information
async def handle_coin_info(update, context):
    user_input = update.message.text
    func = getRespFunc(update)
    loading_message = await func("🔄 Loading information, please wait...")

    user_id = update.effective_user.id
    config = fetch_user_config(user_id)

    coin_info = fetch_coin_info(user_input)
    if coin_info.get("error"):
        await loading_message.delete()
        await func(f"❌ {coin_info['error']}")
        return
    if coin_info:
        # Store state in context.user_data
        context.user_data['coin'] = coin_info['name']
        context.user_data['coin_info'] = coin_info
        context.user_data['action'] = None
        context.user_data['amount'] = None


        # Round and format all values
        price = format_number(coin_info.get('price'))
        price_change_5m = format_number(coin_info.get('price_change_5m'))
        price_change_1h = format_number(coin_info.get('price_change_1h'))
        price_change_6h = format_number(coin_info.get('price_change_6h'))
        price_change_24h = format_number(coin_info.get('price_change_24h'))
        market_cap = format_number(coin_info.get('market_cap'))

        # Generate buy/sell buttons
        keyboard = [
            [InlineKeyboardButton(f"Buy {config.get('buy_left')} SOL", callback_data="buy_left"),
             InlineKeyboardButton("Buy Custom", callback_data="buy_custom"),
             InlineKeyboardButton(f"Buy {config.get('buy_right')} SOL", callback_data="buy_right")],
            [InlineKeyboardButton(f"Sell {config.get('sell_left') * 100}%", callback_data="sell_left"),
             InlineKeyboardButton("Sell Custom", callback_data="sell_custom"),
             InlineKeyboardButton(f"Sell {config.get('sell_right') * 100}%", callback_data="sell_right")],
            [InlineKeyboardButton("Close", callback_data="close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # message = f"🔎 *{coin_info['name']}*\n💰 Price: {coin_info['price']} SOL\nℹ️ {coin_info['description']}"
        # await func(message, reply_markup=reply_markup, parse_mode="Markdown")
            # Create a pretty display message
        message = (
            f"🔎 *{coin_info['name']}* (`{coin_info['symbol']}`)\n"
            f"--------------------------------\n"
            f"💰 *Price*: {price} USD\n"
            f"📈 *Market Cap*: ${market_cap}\n"
            f"--------------------------------\n"
            f"⏳ *Price Changes*:\n"
            f"   - 5m: `{price_change_5m} %`\n"
            f"   - 1h: `{price_change_1h} %`\n"
            f"   - 6h: `{price_change_6h} %`\n"
            f"   - 24h: `{price_change_24h} %`\n"
            f"--------------------------------\n"
            f"🏷️ *Mint Address*: `{coin_info['mint_address']}`\n"
            f"--------------------------------\n"
            f"📝 *Description*: {coin_info['description']}\n"
            f"💻 [DEXSCREENER](https://dexscreener.com/solana/{coin_info['mint_address']})"
        )

        if coin_info['mint_address'].endswith("pump"):
            message += f" | [PUMP.FUN](https://pump.fun/coin/{coin_info['mint_address']})"

        await loading_message.delete()
        # If there's an image URL, attach the image
        if coin_info.get("image_url"):
            await update.message.reply_photo(photo=coin_info['image_url'], caption=message, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await func(message, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        if loading_message: 
            await loading_message.delete()
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
        user_id = update.effective_user.id
        config = fetch_user_config(user_id)
        preset_amount = config.get(action)
        context.user_data['amount'] = preset_amount

        # generate two diff strings for buy and sell. sell values should be converted to percentage
        if action.startswith("sell"):
            amount_str = f"Sell {preset_amount * 100}%"
        else:
            amount_str = f"Buy {preset_amount} SOL"


        await func(
            f"Please confirm: {amount_str}?",
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


            # generate two diff strings for buy and sell. sell values should be converted to percentage
            if action.startswith("sell"):
                amount_str = f"Sell {amount}%"
            else:
                amount_str = f"Buy {amount} SOL"


            await func(
                f"Please confirm: {amount_str}?",
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
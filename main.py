from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from handlers.start_handler import start, menu_handler
from handlers.wallet_handler import wallet_info, add_funds
from handlers.sol_handler import SEND_SOL_AMOUNT, SEND_SOL_ADDRESS, send_sol_amount, send_sol_address
from telegram import BotCommand

from handlers.settings_handler import settings, handle_settings_buttons
from handlers.user_reply import capture_user_reply

import threading
import time

import os
from dotenv import load_dotenv

load_dotenv()

def print_message():
    # check db for snipe contracts
    # try to purchase all snipe contracts
    # if successful, rm snipe contract from db
    # if not successful, wait 5 seconds and try again
    count = 0
    while True:
        print(f"Printed: {count}")
        count += 1
        time.sleep(1)


def main():
    """
    Main function to initialize and start the Telegram bot.
    """

    TELEGRAM_BOT_KEY = os.getenv("TELEGRAM_BOT_KEY")
    application = ApplicationBuilder().token(TELEGRAM_BOT_KEY).build()

    # Define conversation handler for sending SOL
    # conv_handler = ConversationHandler(
    #     entry_points=[CallbackQueryHandler(menu_handler)],
    #     states={
    #         SEND_SOL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_sol_amount)],
    #         SEND_SOL_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_sol_address)],
    #     },
    #     fallbacks=[CommandHandler("start", start)],
    # )
    
    # Set commands
    application.bot.set_my_commands([
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Get help"),
        BotCommand("about", "About the bot"),
        BotCommand("wallet_info", "View wallet info"),
        BotCommand("add_funds", "Add funds to wallet"),
        BotCommand("send_sol", "Withdrawal / Send SOL"),
        BotCommand("trades", "View trades"),
        BotCommand("buy_coin", "Buy coin"),
        BotCommand("sell_coin", "Sell coin"),
        BotCommand("settings", "Settings"),
    ])

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(menu_handler, pattern="main_"))
    application.add_handler(CallbackQueryHandler(handle_settings_buttons, pattern="settings_"))
    application.add_handler(MessageHandler(filters.REPLY & filters.TEXT, capture_user_reply))  # Capture replies

    # application.add_handler(conv_handler)


    # Start a thread to print a message every second
    message_thread = threading.Thread(target=print_message)
    message_thread.daemon = True
    message_thread.start()

    # Start polling
    application.run_polling()

if __name__ == "__main__":
    main()
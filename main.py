from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.about_handler import about_button_handler
from handlers.coin_handler import close, handle_buy_sell, handle_coin_info, handle_confirmation
from handlers.start_handler import about, send_sol, start, menu_handler, start_transaction, trades
from handlers.wallet_handler import trades_callback_handler, wallet_info, add_funds
from handlers.settings_handler import settings, handle_settings_buttons
from handlers.user_reply import capture_user_reply

import os
from dotenv import load_dotenv

load_dotenv()

def main():
    """
    Main function to initialize and start the Telegram bot.
    """

    TELEGRAM_BOT_KEY = os.getenv("TELEGRAM_BOT_KEY")
    application = ApplicationBuilder().token(TELEGRAM_BOT_KEY).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    # application.add_handler(CommandHandler("about", about))
    # application.add_handler(CommandHandler("wallet_info", wallet_info))
    # application.add_handler(CommandHandler("add_funds", add_funds))
    # application.add_handler(CommandHandler("send_sol", send_sol))
    # application.add_handler(CommandHandler("trades", trades))
    # application.add_handler(CommandHandler("buy_coin", start_transaction))
    # application.add_handler(CommandHandler("sell_coin", start_transaction))
    # application.add_handler(CommandHandler("settings", settings))
    application.add_handler(CallbackQueryHandler(menu_handler, pattern="main_"))
    application.add_handler(CallbackQueryHandler(handle_settings_buttons, pattern="settings_"))
    application.add_handler(CallbackQueryHandler(trades_callback_handler, pattern="trades_"))
    application.add_handler(CallbackQueryHandler(about_button_handler, pattern="about_"))
    application.add_handler(MessageHandler(filters.REPLY & filters.TEXT, capture_user_reply))  # Capture replies


    # new logic - Register handlers for coin purchase / sell flow
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_coin_info))  # Default coin info
    application.add_handler(CallbackQueryHandler(handle_buy_sell, pattern="^(buy|sell)_"))
    application.add_handler(MessageHandler(filters.REPLY, capture_user_reply))  # Capture custom amount
    application.add_handler(CallbackQueryHandler(handle_confirmation, pattern="^(confirm|cancel)$"))
    application.add_handler(CallbackQueryHandler(close, pattern="close"))

    # Start polling
    application.run_polling()

if __name__ == "__main__":
    main()
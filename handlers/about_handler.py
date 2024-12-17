from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from handlers.utils import getRespFunc

async def about(update, context):
    """
    Sends a detailed response about the app, including settings, trade details, and fees.
    """
    func = getRespFunc(update)

    detailed_response = """
📖 *About the App*

Welcome to QuickScope Bot! Here's everything you need to know about the app:

---

⚙️ *Settings*:
- Customize your preferences, including buy / sell presets, slippage, and common trading settings.
- Enable or disable features based on your needs.
- All settings are saved and applied to your trades.

💸 *How to Buy and Sell*:
1. **Buy Coin**:
- Go to the *Main Menu* and select *🟢 Buy Coin*.
- Enter the amount of SOL or tokens you want to buy.
- Confirm the transaction and check your updated wallet balance.

2. **Sell Coin**:
- From the *Main Menu*, select *🔴 Sell Coin*.
- Specify the amount of tokens you wish to sell.
- Confirm the transaction and receive the corresponding SOL or equivalent.

** You can also paste a ticker, contract address, or URL to view the latest information and access quick buy / sell options.


↔️ *Trades*:
- View all your active and completed trades in the *Trades* section.
- Manage orders and monitor trade history.

💰 *Fees*:
- We charge a *0.5% fee* on all trade volumes.
- Most other bots charge a 1% minimum fee.
- We offer a lower fee to help you save on trading costs.
- This fee helps us maintain the platform and provide fast, reliable services.

Happy trading! 🚀
    """

    # Add the "Close" button
    keyboard = [
        [InlineKeyboardButton("Close", callback_data="about_close_about")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the detailed response with the Close button
    await func(detailed_response, reply_markup=reply_markup)


async def about_button_handler(update, context):
    """
    Handles button clicks from the main menu.
    """
    query = update.callback_query
    await query.answer()  # Acknowledge button press

    if query.data == "about_close_about":
        await query.message.delete()
        return

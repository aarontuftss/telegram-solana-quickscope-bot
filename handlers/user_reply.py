from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from services.user_config_service import fetch_user_config, update_user_config
from telegram import ForceReply

async def capture_user_reply(update, context):
    """
    Captures and processes the user's reply to a bot's ForceReply message.
    Updates the relevant setting in the database.
    Deletes and re-renders the settings menu.
    """
    user_id = update.effective_user.id
    current_setting = context.user_data.get('current_setting', None)
    original_message = context.user_data.get('original_message', None)

    if not current_setting:
        await update.message.reply_text("No active setting update. Please use the settings menu.")
        return

    try:
        user_input = update.message.text
        new_value = None

        # Validate input based on the setting
        if current_setting in ['sell_left', 'sell_right', 'slippage_buy', 'slippage_sell', 'max_price_impact']:
            # Expect a whole number for percentages (e.g., 24 for 24%)
            if not user_input.isdigit():
                raise ValueError("Input must be a whole number representing a percentage (e.g., 24 for 24%).")
            new_value = float(user_input) / 100  # Convert to decimal for database storage

        elif current_setting in ['buy_left', 'buy_right', 'tp_medium', 'tp_high', 'tp_very_high']:
            # Expect a positive number for SOL amounts (0 - infinity)
            try:
                new_value = float(user_input)
                if new_value < 0:
                    raise ValueError("Input must be a positive number representing SOL (e.g., 4.25 for 4.25 SOL).")
            except ValueError:
                raise ValueError("Input must be a positive number representing SOL (e.g., 4.25 for 4.25 SOL).")

        elif current_setting == 'transaction_priority':
            if user_input.lower() not in ['low', 'medium', 'high']:
                raise ValueError("Input must be 'low', 'medium', or 'high'.")

            new_value = user_input.lower()
        else:
            await update.message.reply_text("Unknown setting. Please try again.")
            return

        # Update the database
        update_user_config(user_id, {current_setting: new_value})

        # Delete the original settings menu if possible
        if original_message:
            try:
                await context.bot.delete_message(chat_id=update.message.chat_id, message_id=original_message)
            except Exception as e:
                print(f"Error deleting message: {e}")

        # Re-render the settings menu
        from handlers.settings_handler import settings
        await settings(update, context)

        # Confirm the update to the user
        await update.message.reply_text(f"✅ Updated **{current_setting.replace('_', ' ').title()}** to {new_value}.")
        
        # Clear the state
        context.user_data.pop('current_setting', None)
        context.user_data.pop('original_message', None)
    except ValueError as e:
        await update.message.reply_text(f"❌ {e}")
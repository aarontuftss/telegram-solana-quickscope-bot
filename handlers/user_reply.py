from telegram import ForceReply
from handlers.coin_handler import capture_amount_reply
from handlers.sol_handler import send_sol_transaction
from services.user_config_service import update_user_config
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

async def capture_user_reply(update, context):
    """
    Captures and processes the user's reply for both settings updates and send_sol flow.
    """
    user_id = update.effective_user.id

    # Handle `send_sol` flow
    send_sol_stage = context.user_data.get('send_sol_stage', None)
    if send_sol_stage:
        await handle_send_sol(update, context, send_sol_stage)
        return

    # Handle settings flow
    current_setting = context.user_data.get('current_setting', None)
    if current_setting:
        await handle_settings_reply(update, context, user_id, current_setting)
        return
    
    current_action = context.user_data.get('action', None)
    if current_action:
        await capture_amount_reply(update, context)
        return


    # Default response for unrecognized input
    await update.message.reply_text("No active operation. Please use a menu option or command.")

async def handle_send_sol(update, context, send_sol_stage):
    """
    Handles the send_sol flow based on the current stage (wallet address or amount).
    """
    user_id = update.effective_user.id

    if send_sol_stage == 'wallet_address':
        wallet_address = update.message.text
        if len(wallet_address) < 30:  # Mock validation
            await update.message.reply_text(
                "Invalid wallet address. Please try again:",
                reply_markup=ForceReply(selective=True)
            )
            return

        context.user_data['wallet_address'] = wallet_address
        context.user_data['send_sol_stage'] = 'amount'
        await update.message.reply_text(
            "Wallet address saved! Now, enter the amount of SOL to send:",
            reply_markup=ForceReply(selective=True)
        )
        return

    if send_sol_stage == 'amount':
        try:
            amount = float(update.message.text)
            if amount <= 0:
                await update.message.reply_text(
                    "Amount must be greater than 0. Please enter a valid amount:",
                    reply_markup=ForceReply(selective=True)
                )
                return

            context.user_data['amount'] = amount
            wallet_address = context.user_data['wallet_address']

            # Fetch user's wallet from Supabase
            user_wallet_response = supabase.table('Wallets').select("*").eq('user_id', user_id).execute()
            if user_wallet_response.data:
                user_wallet = user_wallet_response.data[0]
                sender_wallet = user_wallet['public_key']
                sender_private_key = user_wallet['private_key']  # Handle securely

                # Simulate sending SOL (replace with real implementation)
                transaction_response = send_sol_transaction(
                    sender_wallet, sender_private_key, wallet_address, amount
                )

                if transaction_response['success']:
                    await update.message.reply_text((
                        f"Successfully sent {amount} SOL to {wallet_address}! \n\n"
                        f"------------------------\n"
                        f"View on [Solscan](https://solscan.io/tx/{transaction_response['transaction_signature']})."
                        ),
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                        )
                else:
                    await update.message.reply_text(f"Transaction failed: {transaction_response['error']}")
            else:
                await update.message.reply_text("No wallet information found for your account.")
        except ValueError:
            await update.message.reply_text(
                "Invalid amount. Please enter a numeric value.",
                reply_markup=ForceReply(selective=True)
            )
            return
        finally:
            # Clear `send_sol` state
            context.user_data.pop('send_sol_stage', None)
            context.user_data.pop('wallet_address', None)
            context.user_data.pop('amount', None)
        return

async def handle_settings_reply(update, context, user_id, current_setting):
    """
    Handles replies related to settings updates.
    """
    try:
        user_input = update.message.text
        new_value = None

        # Validate input based on the setting
        if current_setting in ['sell_left', 'sell_right', 'slippage_buy', 'slippage_sell', 'max_price_impact']:
            if not user_input.isdigit():
                raise ValueError("Input must be a whole number representing a percentage.")
            new_value = float(user_input) / 100

        elif current_setting in ['buy_left', 'buy_right', 'tp_medium', 'tp_high', 'tp_very_high']:
            new_value = float(user_input)
            if new_value < 0:
                raise ValueError("Input must be a positive number.")

        elif current_setting == 'transaction_priority':
            if user_input.lower() not in ['low', 'medium', 'high']:
                raise ValueError("Input must be 'low', 'medium', or 'high'.")
            new_value = user_input.lower()

        else:
            await update.message.reply_text("Unknown setting. Please try again.")
            return

        # Update the database
        update_user_config(user_id, {current_setting: new_value})

        # new 
        # Delete the original settings menu if possible
        original_message = context.user_data.get('original_message', None)
        if original_message:
            try:
                await context.bot.delete_message(chat_id=update.message.chat_id, message_id=original_message)
            except Exception as e:
                print(f"Error deleting message: {e}")

        # Re-render the settings menu
        from handlers.settings_handler import settings
        await settings(update, context)

        await update.message.reply_text(f"✅ Updated **{current_setting.replace('_', ' ').title()}** to {new_value}.")
        context.user_data.pop('current_setting', None)
        context.user_data.pop('original_message', None)
    except ValueError as e:
        await update.message.reply_text(f"❌ {e}")
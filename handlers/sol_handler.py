from telegram import Update
from telegram.ext import ConversationHandler
from services.sol_service import send_sol_transaction

SEND_SOL_AMOUNT, SEND_SOL_ADDRESS = range(2)

async def send_sol_amount(update: Update, context):
    """
    Captures the amount of SOL to send.
    """
    try:
        amount = float(update.message.text)
        if amount <= 0:
            await update.message.reply_text("Please enter a valid amount greater than 0.")
            return SEND_SOL_AMOUNT

        context.user_data["amount"] = amount
        await update.message.reply_text("Enter the recipient's wallet address:")
        return SEND_SOL_ADDRESS
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")
        return SEND_SOL_AMOUNT

async def send_sol_address(update: Update, context):
    """
    Captures the recipient's wallet address and performs the transaction.
    """
    recipient_address = update.message.text
    amount = context.user_data.get("amount")
    sender_id = update.effective_user.id

    try:
        result = send_sol_transaction(sender_id, recipient_address, amount)
        await update.message.reply_text(f"Transaction successful! Signature: {result['signature']}")
    except Exception as e:
        await update.message.reply_text(f"Transaction failed: {str(e)}")
        return ConversationHandler.END

    return ConversationHandler.END
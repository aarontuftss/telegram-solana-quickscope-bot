from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from services.user_config_service import fetch_user_config, update_user_config
from telegram import ForceReply

async def settings(update, context):
    """
    Displays the Settings menu with dynamic buttons based on the user's current config.
    """
    context.user_data.clear()
    user_id = update.effective_user.id

    # Fetch user configuration
    config = fetch_user_config(user_id)
    if not config:
        await update.callback_query.message.reply_text("Error fetching your settings. Please try again.")
        return

    priority_config = {
        'medium': InlineKeyboardButton(f"🔘 Medium: {config['tp_medium']} SOL", callback_data="settings_set_tp_medium"),
        'high': InlineKeyboardButton(f"🔘 High: {config['tp_high']} SOL", callback_data="settings_set_tp_high"),
        'very_high': InlineKeyboardButton(f"🔘 Very High: {config['tp_very_high']} SOL", callback_data="settings_set_tp_very_high"),
    }

    # Generate buttons dynamically based on the current config
    keyboard = [
        [InlineKeyboardButton(f"🔘 Sell Initial: {'Enabled' if config['sell_initial'] else 'Disabled'}",
                              callback_data="settings_toggle_sell_initial")],
        [InlineKeyboardButton(f"🔘 Buy Left: {config['buy_left']} SOL", callback_data="settings_set_buy_left"),
         InlineKeyboardButton(f"🔘 Buy Right: {config['buy_right']} SOL", callback_data="settings_set_buy_right")],

        [InlineKeyboardButton(f"🔘 Sell Left: {config['sell_left']*100:.1f}%", callback_data="settings_set_sell_left"),
         InlineKeyboardButton(f"🔘 Sell Right: {config['sell_right']*100:.1f}%", callback_data="settings_set_sell_right")],

        [InlineKeyboardButton(f"🔘 Slippage Buy: {config['slippage_buy']*100:.1f}%", callback_data="settings_set_slippage_buy"),
         InlineKeyboardButton(f"🔘 Slippage Sell: {config['slippage_sell']*100:.1f}%", callback_data="settings_set_slippage_sell")],

        [InlineKeyboardButton(f"🔘 Max Price Impact: {config['max_price_impact']*100:.1f}%", callback_data="settings_set_max_price_impact")],

        [InlineKeyboardButton(f"🔘 MEV Protect: {'Enabled' if config['mev_protect'] else 'Disabled'}", callback_data="settings_toggle_mev_protect")],

        [InlineKeyboardButton(f"🔘 Priority: {config['transaction_priority']}", callback_data="settings_set_transaction_priority"),
        priority_config[config['transaction_priority']]],

        [InlineKeyboardButton("Close", callback_data="settings_close_settings")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the settings menu to the user
    # await update.callback_query.message.reply_text("⚙️ Settings Menu ⚙️", reply_markup=reply_markup)
    if hasattr(update, 'callback_query') and update.callback_query:
        # Triggered by a button press
        await update.callback_query.message.reply_text("⚙️ Settings Menu ⚙️", reply_markup=reply_markup)
    elif hasattr(update, 'message') and update.message:
        # Triggered by a command
        await update.message.reply_text("⚙️ Settings Menu ⚙️", reply_markup=reply_markup)



async def handle_settings_buttons(update, context):
    """
    Handles button presses from the Settings menu.
    """
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    config_update = {}
    # Handle each button action
    if query.data == "settings_toggle_sell_initial":
        current_value = fetch_user_config(user_id)['sell_initial']
        config_update['sell_initial'] = not current_value
    elif query.data == "settings_toggle_mev_protect":
        current_value = fetch_user_config(user_id)['mev_protect']
        config_update['mev_protect'] = not current_value
    # Handle user input buttons with ForceReply
    elif query.data == "settings_set_buy_left":
        await query.message.reply_text(
            "Enter the new **Buy Left** value (in SOL):",
            reply_markup=ForceReply(selective=True)
        )
        context.user_data['current_setting'] = 'buy_left'
        return
    elif query.data == "settings_set_buy_right":
        await query.message.reply_text(
            "Enter the new **Buy Right** value (in SOL):",
            reply_markup=ForceReply(selective=True)
        )
        context.user_data['current_setting'] = 'buy_right'
        return
    elif query.data == "settings_set_slippage_buy":
        await query.message.reply_text(
            "Enter the new **Buy Slippage** value (in %):",
            reply_markup=ForceReply(selective=True)
        )
        context.user_data['current_setting'] = 'slippage_buy'
        return
    elif query.data == "settings_set_slippage_sell":
        await query.message.reply_text(
            "Enter the new **Sell Slippage** value (in %):",
            reply_markup=ForceReply(selective=True)
        )
        context.user_data['current_setting'] = 'slippage_sell'
        return
    elif query.data == "settings_set_max_price_impact":
        await query.message.reply_text(
            "Enter the new **Max Price Impact** value (in %):",
            reply_markup=ForceReply(selective=True)
        )
        context.user_data['current_setting'] = 'max_price_impact'
        return
    elif query.data == "settings_set_transaction_priority":
        priotity_opts = ['medium', 'high', 'very_high']
        current_value = fetch_user_config(user_id)['transaction_priority']
        config_update['transaction_priority'] = priotity_opts[(priotity_opts.index(current_value) + 1) % len(priotity_opts)]
    elif query.data == "settings_set_tp_medium":
        await query.message.reply_text(
            "Enter the new **Priority** amount (in SOL):",
            reply_markup=ForceReply(selective=True)
        )
        context.user_data['current_setting'] = 'tp_medium'
        return
    elif query.data == "settings_set_tp_high":
        await query.message.reply_text(
            "Enter the new **Priority** amount (in SOL):",
            reply_markup=ForceReply(selective=True)
        )
        context.user_data['current_setting'] = 'tp_high'
        return
    elif query.data == "settings_set_tp_very_high":
        await query.message.reply_text(
            "Enter the new **Priority** amount (in SOL):",
            reply_markup=ForceReply(selective=True)
        )
        context.user_data['current_setting'] = 'tp_very_high'
        return
    elif query.data == "settings_close_settings":
        await query.message.delete()
        return

        
    
    # Update the user's config in Supabase
    if config_update:
        update_user_config(user_id, config_update)

    # Re-render the settings menu
    await query.message.delete()
    await settings(update, context)
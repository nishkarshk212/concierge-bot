import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import group_settings, DEFAULT_SETTINGS
from database import save_settings
from font import apply_font
from ui import get_recurring_messages_keyboard

async def recurring_message_job(context: ContextTypes.DEFAULT_TYPE):
    """Job that sends recurring messages to the group."""
    job = context.job
    chat_id = job.chat_id
    
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    recurring = settings.get("recurring_messages", {})
    
    if not recurring.get("enabled", False):
        return
    
    message_type = recurring.get("message_type", "text")
    text = recurring.get("message_text", "")
    media_id = recurring.get("message_media_id")
    buttons = recurring.get("message_buttons", [])
    
    # Build keyboard if buttons exist
    keyboard = []
    if buttons:
        for btn in buttons:
            keyboard.append([InlineKeyboardButton(btn["label"], url=btn["url"])])
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    try:
        if message_type == "photo" and media_id:
            await context.bot.send_photo(
                chat_id=chat_id, 
                photo=media_id, 
                caption=text, 
                reply_markup=reply_markup, 
                parse_mode='HTML'
            )
        elif message_type == "video" and media_id:
            await context.bot.send_video(
                chat_id=chat_id, 
                video=media_id, 
                caption=text, 
                reply_markup=reply_markup, 
                parse_mode='HTML'
            )
        elif message_type == "animation" and media_id:
            await context.bot.send_animation(
                chat_id=chat_id, 
                animation=media_id, 
                caption=text, 
                reply_markup=reply_markup, 
                parse_mode='HTML'
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id, 
                text=text, 
                reply_markup=reply_markup, 
                parse_mode='HTML'
            )
    except Exception as e:
        logging.error(f"Error sending recurring message to {chat_id}: {e}")

async def toggle_recurring_enabled(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle recurring messages on/off."""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    if chat_id not in group_settings:
        await save_settings(chat_id)
    
    settings = group_settings[chat_id]
    if "recurring_messages" not in settings:
        settings["recurring_messages"] = DEFAULT_SETTINGS["recurring_messages"].copy()
    
    settings["recurring_messages"]["enabled"] = not settings["recurring_messages"].get("enabled", False)
    await save_settings(chat_id)
    
    # Update job
    await update_recurring_job(context, chat_id)
    
    keyboard = await get_recurring_messages_keyboard(chat_id)
    await query.edit_message_text(
        apply_font("🔄 Recurring Messages Settings"), 
        reply_markup=keyboard, 
        parse_mode='HTML'
    )

async def set_recurring_type_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set recurring message type to text."""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    settings = group_settings[chat_id]
    settings["recurring_messages"]["message_type"] = "text"
    await save_settings(chat_id)
    
    keyboard = await get_recurring_messages_keyboard(chat_id)
    await query.edit_message_text(
        apply_font("🔄 Recurring Messages Settings"), 
        reply_markup=keyboard, 
        parse_mode='HTML'
    )

async def set_recurring_type_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set recurring message type to photo."""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    settings = group_settings[chat_id]
    settings["recurring_messages"]["message_type"] = "photo"
    await save_settings(chat_id)
    
    keyboard = await get_recurring_messages_keyboard(chat_id)
    await query.edit_message_text(
        apply_font("🔄 Recurring Messages Settings"), 
        reply_markup=keyboard, 
        parse_mode='HTML'
    )

async def set_recurring_type_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set recurring message type to video."""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    settings = group_settings[chat_id]
    settings["recurring_messages"]["message_type"] = "video"
    await save_settings(chat_id)
    
    keyboard = await get_recurring_messages_keyboard(chat_id)
    await query.edit_message_text(
        apply_font("🔄 Recurring Messages Settings"), 
        reply_markup=keyboard, 
        parse_mode='HTML'
    )

async def set_recurring_type_animation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set recurring message type to animation/GIF."""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    settings = group_settings[chat_id]
    settings["recurring_messages"]["message_type"] = "animation"
    await save_settings(chat_id)
    
    keyboard = await get_recurring_messages_keyboard(chat_id)
    await query.edit_message_text(
        apply_font("🔄 Recurring Messages Settings"), 
        reply_markup=keyboard, 
        parse_mode='HTML'
    )

async def set_recurring_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for setting recurring message text."""
    chat_id = context.user_data.get('setting_chat_id')
    if chat_id:
        settings = group_settings[chat_id]
        settings["recurring_messages"]["message_text"] = update.message.text
        await save_settings(chat_id)
        await update.message.reply_text(apply_font("✅ Recurring message text updated!"))
    return ConversationHandler.END

async def set_recurring_media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for setting recurring message media."""
    chat_id = context.user_data.get('setting_chat_id')
    if chat_id:
        settings = group_settings[chat_id]
        msg = update.message
        
        # Get media file_id based on type
        if msg.photo:
            media_id = msg.photo[-1].file_id
            media_type = "photo"
        elif msg.video:
            media_id = msg.video.file_id
            media_type = "video"
        elif msg.animation:
            media_id = msg.animation.file_id
            media_type = "animation"
        else:
            await update.message.reply_text(apply_font("❌ Please send a photo, video, or animation."))
            return ConversationHandler.END
        
        settings["recurring_messages"]["message_media_id"] = media_id
        settings["recurring_messages"]["message_type"] = media_type
        if msg.caption:
            settings["recurring_messages"]["message_text"] = msg.caption
        
        await save_settings(chat_id)
        await update.message.reply_text(apply_font("✅ Recurring message media updated!"))
    return ConversationHandler.END

async def add_recurring_button_label_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for adding button label."""
    context.user_data['recurring_btn_label'] = update.message.text
    await update.message.reply_text(apply_font("Now send the URL for this button:"))
    return ConversationHandler.END

async def add_recurring_button_url_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for adding button URL."""
    chat_id = context.user_data.get('setting_chat_id')
    label = context.user_data.get('recurring_btn_label')
    url = update.message.text
    
    if chat_id and label and url.startswith("http"):
        settings = group_settings[chat_id]
        if "message_buttons" not in settings["recurring_messages"]:
            settings["recurring_messages"]["message_buttons"] = []
        
        settings["recurring_messages"]["message_buttons"].append({"label": label, "url": url})
        await save_settings(chat_id)
        await update.message.reply_text(apply_font(f"✅ Button '{label}' added!"))
    else:
        await update.message.reply_text(apply_font("❌ Invalid URL! Must start with http:// or https://"))
    
    return ConversationHandler.END

async def remove_recurring_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a recurring message button."""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    button_idx = int(query.data.split("_")[-1])
    
    settings = group_settings[chat_id]
    buttons = settings["recurring_messages"].get("message_buttons", [])
    
    if 0 <= button_idx < len(buttons):
        removed = buttons.pop(button_idx)
        await save_settings(chat_id)
        await query.answer(f"Removed button: {removed['label']}")
    
    keyboard = await get_recurring_messages_keyboard(chat_id)
    await query.edit_message_text(
        apply_font("🔄 Recurring Messages Settings"), 
        reply_markup=keyboard, 
        parse_mode='HTML'
    )

async def change_recurring_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Change the recurring message interval."""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    settings = group_settings[chat_id]
    recurring = settings["recurring_messages"]
    
    # Parse callback data: recurring_interval_minutes_5 or recurring_interval_hours_-1
    parts = query.data.split("_")
    unit = parts[2]  # minutes or hours
    change = int(parts[3])
    
    if unit == "minutes":
        current = recurring.get("interval_minutes", 5)
        current += change
        if current < 1:
            current = 1
        recurring["interval_minutes"] = current
    elif unit == "hours":
        current = recurring.get("interval_hours", 0)
        current += change
        if current < 0:
            current = 0
        recurring["interval_hours"] = current
    
    await save_settings(chat_id)
    await update_recurring_job(context, chat_id)
    
    keyboard = await get_recurring_messages_keyboard(chat_id)
    await query.edit_message_text(
        apply_font("🔄 Recurring Messages Settings"), 
        reply_markup=keyboard, 
        parse_mode='HTML'
    )

async def update_recurring_job(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Update or remove the recurring message job."""
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    recurring = settings.get("recurring_messages", {})
    
    # Remove existing job for this chat
    current_jobs = context.job_queue.get_jobs_by_name(f"recurring_{chat_id}")
    for job in current_jobs:
        job.schedule_removal()
    
    # Add new job if enabled
    if recurring.get("enabled", False):
        interval_minutes = recurring.get("interval_minutes", 5)
        interval_hours = recurring.get("interval_hours", 0)
        total_seconds = (interval_hours * 3600) + (interval_minutes * 60)
        
        if total_seconds > 0:
            context.job_queue.run_repeating(
                recurring_message_job,
                interval=total_seconds,
                first=total_seconds,
                chat_id=chat_id,
                name=f"recurring_{chat_id}"
            )

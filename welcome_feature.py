import html
import re
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import group_settings, DEFAULT_SETTINGS, LOG_GROUP_ID
from database import save_settings
from font import apply_font
from common import (
    SET_WELCOME_TEXT, SET_WELCOME_MEDIA, ADD_WELCOME_BUTTON_LABEL, ADD_WELCOME_BUTTON_URL, 
    SET_WELCOME_AUTODEL, SET_FLOOD_MSGS, SET_FLOOD_TIME, SET_GROUP_LINK
)

async def delete_msg_job(context: ContextTypes.DEFAULT_TYPE):
    """Delete a message after auto-delete timer expires."""
    job = context.job
    try:
        logging.info(f"Auto-delete: Deleting message {job.data} in chat {job.chat_id}")
        await context.bot.delete_message(chat_id=job.chat_id, message_id=job.data)
        logging.info(f"Auto-delete: Successfully deleted message {job.data}")
    except Exception as e:
        logging.error(f"Auto-delete: Failed to delete message {job.data} in chat {job.chat_id}: {e}")

async def set_welcome_autodel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.user_data.get('setting_chat_id')
    if chat_id:
        try:
            val = int(update.message.text)
            if val < 0:
                await update.message.reply_text(apply_font("Please enter a positive number (0 to disable)."))
                return SET_WELCOME_AUTODEL
            group_settings[chat_id]["welcome_autodelete"] = val
            await save_settings(chat_id)
            
            if val > 0:
                status = f"✅ Auto-delete set to {val} seconds!"
                info = f"\n\n📝 Welcome messages will be automatically deleted after {val} seconds.\n💾 Settings saved successfully!"
            else:
                status = "❌ Auto-delete disabled!"
                info = "\n\n📝 Welcome messages will no longer be auto-deleted.\n💾 Settings saved successfully!"
            
            await update.message.reply_text(apply_font(status + info))
        except ValueError:
            await update.message.reply_text(apply_font("Invalid number! Please send seconds as a number."))
            return SET_WELCOME_AUTODEL
    return ConversationHandler.END

async def set_welcome_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.user_data.get('setting_chat_id')
    if chat_id:
        group_settings[chat_id]["welcome_text"] = update.message.text
        await save_settings(chat_id)
        await update.message.reply_text(apply_font("Welcome text updated!"))
    return ConversationHandler.END

async def set_welcome_media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.user_data.get('setting_chat_id')
    if chat_id:
        media = update.message.photo[-1] if update.message.photo else (update.message.video or update.message.animation)
        if media:
            group_settings[chat_id]["welcome_media"] = media.file_id
            group_settings[chat_id]["welcome_media_type"] = "photo" if update.message.photo else ("video" if update.message.video else "animation")
            await save_settings(chat_id)
            await update.message.reply_text(apply_font("Welcome media updated!"))
    return ConversationHandler.END

async def add_welcome_button_label_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['btn_label'] = update.message.text
    await update.message.reply_text(apply_font("Send the URL for this button:"))
    return ADD_WELCOME_BUTTON_URL

async def add_welcome_button_url_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.user_data.get('setting_chat_id')
    label = context.user_data.get('btn_label')
    url = update.message.text
    if chat_id and label and url.startswith("http"):
        if "welcome_buttons" not in group_settings[chat_id]:
            group_settings[chat_id]["welcome_buttons"] = []
        group_settings[chat_id]["welcome_buttons"].append({"label": label, "url": url})
        await save_settings(chat_id)
        await update.message.reply_text(apply_font("Button added!"))
    else:
        await update.message.reply_text(apply_font("Invalid URL! Start with http:// or https://"))
    return ConversationHandler.END

async def preview_welcome(update: Update, context, chat_id, target_user=None, chat_title=None):
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    text = settings.get("welcome_text", "Welcome!")
    media_id = settings.get("welcome_media")
    media_type = settings.get("welcome_media_type")
    buttons = settings.get("welcome_buttons", [])
    
    # Process placeholders
    if not target_user:
        target_user = update.effective_user
    
    if not chat_title:
        if update.effective_chat:
            chat_title = update.effective_chat.title
        elif update.chat_member:
            chat_title = update.chat_member.chat.title
        else:
            chat_title = "Group"

    now = datetime.now()
    
    # Values to be inserted
    user_id = str(target_user.id)
    first_name = html.escape(target_user.first_name)
    last_name = html.escape(target_user.last_name or "")
    full_name = html.escape(f"{target_user.first_name} {target_user.last_name or ''}".strip())
    username = html.escape(f"@{target_user.username}" if target_user.username else target_user.first_name)
    group_name = html.escape(chat_title)
    mention = target_user.mention_html() # Already HTML escaped by PTB
    lang = html.escape(target_user.language_code or "en")
    date_str = now.strftime("%d/%m/%Y")
    time_str = now.strftime("%H:%M:%S")
    weekday_str = now.strftime("%A")

    placeholders = {
        "{ID}": user_id,
        "{NAME}": first_name,
        "{SURNAME}": last_name,
        "{NAMESURNAME}": full_name,
        "{LANG}": lang,
        "{DATE}": date_str,
        "{TIME}": time_str,
        "{WEEKDAY}": weekday_str,
        "{MENTION}": mention,
        "{USERNAME}": username,
        "{GROUPNAME}": group_name,
        "{RULES}": "/rules"
    }
    
    # Case-insensitive replacement for all placeholders
    for key, val in placeholders.items():
        # Use regex with re.IGNORECASE to match {ID}, {id}, {Id}, etc.
        pattern = re.compile(re.escape(key), re.IGNORECASE)
        text = pattern.sub(str(val), text)
    
    logging.info(f"Welcome text after replacement: {text}")
    
    keyboard = [[InlineKeyboardButton(b['label'], url=b['url'])] for b in buttons]
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    sent_msg = None
    target_chat_id = chat_id # Use the passed chat_id
    if media_id:
        try:
            if media_type == "photo":
                sent_msg = await context.bot.send_photo(chat_id=target_chat_id, photo=media_id, caption=text, reply_markup=reply_markup, parse_mode='HTML')
            elif media_type == "video":
                sent_msg = await context.bot.send_video(chat_id=target_chat_id, video=media_id, caption=text, reply_markup=reply_markup, parse_mode='HTML')
            elif media_type == "animation":
                sent_msg = await context.bot.send_animation(chat_id=target_chat_id, animation=media_id, caption=text, reply_markup=reply_markup, parse_mode='HTML')
        except Exception as e:
            logging.error(f"Failed to send welcome media: {e}")
            # Fallback to text if media fails
            sent_msg = await context.bot.send_message(chat_id=target_chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        sent_msg = await context.bot.send_message(chat_id=target_chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

    # Auto-deletion logic
    autodel_time = settings.get("welcome_autodelete", 0)
    if sent_msg and autodel_time > 0:
        logging.info(f"Scheduling auto-delete for message {sent_msg.message_id} in {autodel_time} seconds (chat: {target_chat_id})")
        context.job_queue.run_once(delete_msg_job, autodel_time, chat_id=target_chat_id, data=sent_msg.message_id)
        logging.info(f"Auto-delete job scheduled successfully")

async def notify_bot_added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, chat_title: str, added_by_user=None):
    """
    Send notification to log group when bot is added to a new group.
    """
    try:
        # Get bot info
        bot = await context.bot.get_me()
        
        # Get member count
        member_count = await context.bot.get_chat_members_count(chat_id)
        
        # Get chat type
        chat_type = "Group" if update.effective_chat and update.effective_chat.type in ["group", "supergroup"] else "Channel"
        
        # Format added by info
        added_by_text = "Unknown"
        if added_by_user:
            username = f"@{added_by_user.username}" if added_by_user.username else added_by_user.first_name
            added_by_text = f"{username} [{added_by_user.id}]"
        
        # Create notification message
        notification = (
            f"➕ <b>ʙᴏᴛ ᴀᴅᴅᴇᴅ ᴛᴏ ɴᴇᴡ {chat_type.upper()}</b>\n\n"
            f"❅─────✧❅✦❅✧─────❅\n\n"
            f"📝 <b>{chat_title}</b>\n"
            f"🆔 <b>ɢʀᴏᴜᴘ ɪᴅ:</b> <code>{chat_id}</code>\n"
            f"👥 <b>ᴍᴇᴍʙᴇʀs:</b> {member_count}\n"
            f"➕ <b>ᴀᴅᴅᴇᴅ ʙʏ:</b> {added_by_text}\n"
            f"🤖 <b>ʙᴏᴛ:</b> {bot.mention_html()}\n"
            f"📅 <b>ᴅᴀᴛᴇ:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
            f"✅ <b>sᴛᴀᴛᴜs:</b> Ready to serve!"
        )
        
        # Add button to view group
        keyboard = [[InlineKeyboardButton("👁️ ᴠɪᴇᴡ ɢʀᴏᴜᴘ", url=f"https://t.me/{chat_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            LOG_GROUP_ID, 
            notification, 
            parse_mode='HTML',
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        
        logging.info(f"Bot added notification sent for group: {chat_title} ({chat_id})")
        
    except Exception as e:
        logging.error(f"Error sending bot added notification: {e}")

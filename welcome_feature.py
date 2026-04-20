import html
import re
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import group_settings, DEFAULT_SETTINGS
from database import save_settings
from font import apply_font
from common import (
    SET_WELCOME_TEXT, SET_WELCOME_MEDIA, ADD_WELCOME_BUTTON_LABEL, ADD_WELCOME_BUTTON_URL, 
    SET_WELCOME_AUTODEL, SET_FLOOD_MSGS, SET_FLOOD_TIME, SET_GROUP_LINK
)

async def delete_msg_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.delete_message(chat_id=job.chat_id, message_id=job.data)
    except Exception:
        pass

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
            status = f"set to {val} seconds" if val > 0 else "disabled"
            await update.message.reply_text(apply_font(f"Welcome auto-deletion {status}!"))
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
        chat_title = update.effective_chat.title if update.effective_chat else "Group"

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
        "{ɪᴅ}": user_id, "{ID}": user_id, "{id}": user_id,
        "{ɴᴀᴍᴇ}": first_name, "{NAME}": first_name, "{name}": first_name,
        "{sᴜʀɴᴀᴍᴇ}": last_name, "{SURNAME}": last_name, "{surname}": last_name,
        "{ɴᴀᴍᴇsᴜʀɴᴀᴍᴇ}": full_name, "{NAMESURNAME}": full_name, "{namesurname}": full_name,
        "{ʟᴀɴɢ}": lang, "{LANG}": lang, "{lang}": lang,
        "{ᴅᴀᴛᴇ}": date_str, "{DATE}": date_str, "{date}": date_str,
        "{ᴛɪᴍᴇ}": time_str, "{TIME}": time_str, "{time}": time_str,
        "{ᴡᴇᴇᴋᴅᴀʏ}": weekday_str, "{WEEKDAY}": weekday_str, "{weekday}": weekday_str,
        "{ᴍᴇɴᴛɪᴏɴ}": mention, "{MENTION}": mention, "{mention}": mention,
        "{ᴜsᴇʀɴᴀᴍᴇ}": username, "{USERNAME}": username, "{username}": username,
        "{ɢʀᴏᴜᴘɴᴀᴍᴇ}": group_name, "{GROUPNAME}": group_name, "{groupname}": group_name,
        "{ʀᴜʟᴇs}": "/rules", "{RULES}": "/rules", "{rules}": "/rules"
    }
    
    for key, val in placeholders.items():
        pattern = re.escape(key)
        text = re.sub(pattern, str(val), text, flags=re.IGNORECASE)
    
    logging.info(f"Welcome text after replacement: {text}")
    
    keyboard = [[InlineKeyboardButton(b['label'], url=b['url'])] for b in buttons]
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    sent_msg = None
    target_chat_id = update.effective_chat.id
    if media_id:
        if media_type == "photo":
            sent_msg = await context.bot.send_photo(chat_id=target_chat_id, photo=media_id, caption=text, reply_markup=reply_markup, parse_mode='HTML')
        elif media_type == "video":
            sent_msg = await context.bot.send_video(chat_id=target_chat_id, video=media_id, caption=text, reply_markup=reply_markup, parse_mode='HTML')
        elif media_type == "animation":
            sent_msg = await context.bot.send_animation(chat_id=target_chat_id, animation=media_id, caption=text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        sent_msg = await context.bot.send_message(chat_id=target_chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

    # Auto-deletion logic
    autodel_time = settings.get("welcome_autodelete", 0)
    if sent_msg and autodel_time > 0:
        context.job_queue.run_once(delete_msg_job, autodel_time, chat_id=target_chat_id, data=sent_msg.message_id)

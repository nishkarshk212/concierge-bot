from telegram import Update
from telegram.ext import ContextTypes
from config import group_settings, DEFAULT_SETTINGS, get_default_settings
from database import save_settings
from font import apply_font
from common import check_permission, check_admin_permissions

async def filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if user has required admin permissions (can_change_info AND can_restrict_members)
    has_perm, error_msg = await check_admin_permissions(
        update, context, 
        required_perms=['can_change_info', 'can_restrict_members']
    )
    if not has_perm:
        await update.message.reply_text(error_msg)
        return

    chat_id = update.effective_chat.id
    if not context.args:
        await update.message.reply_text(apply_font("Usage: /filter <trigger> (as reply) OR /filter <trigger> <reply text>"))
        return

    trigger = context.args[0].lower()
    
    if update.message.reply_to_message:
        # Reply mode
        reply_msg = update.message.reply_to_message
        filter_data = {"type": "text", "text": reply_msg.text or reply_msg.caption}
        
        if reply_msg.photo:
            filter_data = {"type": "photo", "file_id": reply_msg.photo[-1].file_id, "text": reply_msg.caption}
        elif reply_msg.video:
            filter_data = {"type": "video", "file_id": reply_msg.video.file_id, "text": reply_msg.caption}
        elif reply_msg.animation:
            filter_data = {"type": "animation", "file_id": reply_msg.animation.file_id, "text": reply_msg.caption}
        elif reply_msg.document:
            filter_data = {"type": "document", "file_id": reply_msg.document.file_id, "text": reply_msg.caption}
        elif reply_msg.sticker:
            filter_data = {"type": "sticker", "file_id": reply_msg.sticker.file_id}
        elif reply_msg.voice:
            filter_data = {"type": "voice", "file_id": reply_msg.voice.file_id}
        elif reply_msg.video_note:
            filter_data = {"type": "video_note", "file_id": reply_msg.video_note.file_id}
        elif reply_msg.audio:
            filter_data = {"type": "audio", "file_id": reply_msg.audio.file_id, "text": reply_msg.caption}
            
    elif len(context.args) >= 2:
        # Text mode
        reply_text = " ".join(context.args[1:])
        filter_data = {"type": "text", "text": reply_text}
    else:
        await update.message.reply_text(apply_font("Usage: /filter <trigger> (as reply) OR /filter <trigger> <reply text>"))
        return

    if chat_id not in group_settings:
        group_settings[chat_id] = get_default_settings()
    if "filters" not in group_settings[chat_id]:
        group_settings[chat_id]["filters"] = {}

    group_settings[chat_id]["filters"][trigger] = filter_data
    await save_settings(chat_id)
    await update.message.reply_text(apply_font(f"Filter '{trigger}' added!"))

async def filters_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check admin permissions
    has_perm, error_msg = await check_admin_permissions(
        update, context, 
        required_perms=['can_change_info', 'can_restrict_members']
    )
    if not has_perm:
        await update.message.reply_text(error_msg)
        return

    chat_id = update.effective_chat.id
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    filters = settings.get("filters", {})

    if not filters:
        await update.message.reply_text(apply_font("No filters set for this chat."))
        return

    filter_list = ""
    for trigger, data in filters.items():
        content_type = data.get("type", "text")
        filter_list += f"• <b>{trigger}</b> ({content_type})\n"
        
    await update.message.reply_text(f"<b>{apply_font('Current Filters:')}</b>\n{filter_list}", parse_mode='HTML')

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check admin permissions
    has_perm, error_msg = await check_admin_permissions(
        update, context, 
        required_perms=['can_change_info', 'can_restrict_members']
    )
    if not has_perm:
        await update.message.reply_text(error_msg)
        return

    chat_id = update.effective_chat.id
    if not context.args:
        await update.message.reply_text(apply_font("Usage: /stop <trigger>"))
        return

    trigger = context.args[0].lower()

    if chat_id in group_settings and "filters" in group_settings[chat_id] and trigger in group_settings[chat_id]["filters"]:
        del group_settings[chat_id]["filters"][trigger]
        await save_settings(chat_id)
        await update.message.reply_text(apply_font(f"Filter '{trigger}' removed!"))
    else:
        await update.message.reply_text(apply_font(f"Filter '{trigger}' not found."))

async def stopall_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check admin permissions
    has_perm, error_msg = await check_admin_permissions(
        update, context, 
        required_perms=['can_change_info', 'can_restrict_members']
    )
    if not has_perm:
        await update.message.reply_text(error_msg)
        return

    chat_id = update.effective_chat.id
    if chat_id in group_settings and "filters" in group_settings[chat_id]:
        group_settings[chat_id]["filters"] = {}
        await save_settings(chat_id)
        await update.message.reply_text(apply_font("All filters removed for this chat!"))
    else:
        await update.message.reply_text(apply_font("No filters to remove for this chat."))

async def handle_filters(update: Update, context: ContextTypes.DEFAULT_TYPE, settings: dict):
    """Checks if a message triggers any filter and replies accordingly."""
    if not update.message or not update.message.text:
        return False
        
    filters_dict = settings.get("filters", {})
    text_lower = update.message.text.lower()
    
    for trigger, data in filters_dict.items():
        if trigger in text_lower:
            if isinstance(data, str):
                # Backward compatibility
                await update.message.reply_text(data, parse_mode='HTML')
            else:
                msg_type = data.get("type", "text")
                file_id = data.get("file_id")
                text = data.get("text")
                
                if msg_type == "text":
                    await update.message.reply_text(text, parse_mode='HTML')
                elif msg_type == "photo":
                    await update.message.reply_photo(file_id, caption=text, parse_mode='HTML')
                elif msg_type == "video":
                    await update.message.reply_video(file_id, caption=text, parse_mode='HTML')
                elif msg_type == "animation":
                    await update.message.reply_animation(file_id, caption=text, parse_mode='HTML')
                elif msg_type == "document":
                    await update.message.reply_document(file_id, caption=text, parse_mode='HTML')
                elif msg_type == "sticker":
                    try:
                        await update.message.reply_sticker(file_id)
                    except Exception as e:
                        logging.error(f"Error sending sticker reply: {e}")
                elif msg_type == "voice":
                    await update.message.reply_voice(file_id)
                elif msg_type == "video_note":
                    await update.message.reply_video_note(file_id)
                elif msg_type == "audio":
                    await update.message.reply_audio(file_id, caption=text, parse_mode='HTML')
            return True
    return False

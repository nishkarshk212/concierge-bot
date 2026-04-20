import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import group_settings, DEFAULT_SETTINGS
from database import save_settings
from font import apply_font
import copy


async def handle_bot_protection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles bot protection - automatically kicks bots when they are added to the group.
    This function should be called when new chat members join.
    """
    if not update.effective_chat or update.effective_chat.type == "private":
        return False

    chat_id = update.effective_chat.id
    
    # Ensure chat settings are loaded
    if chat_id not in group_settings:
        group_settings[chat_id] = copy.deepcopy(DEFAULT_SETTINGS)
    
    settings = group_settings[chat_id]
    
    # Check if bot protection is enabled
    if not settings.get("bot_protection_enabled", False):
        return False

    # Check if there are new chat members
    if not update.message or not update.message.new_chat_members:
        return False

    bot_id = context.bot.id
    
    for new_member in update.message.new_chat_members:
        # Skip if it's the bot itself
        if new_member.id == bot_id:
            continue
            
        # Check if the new member is a bot
        if new_member.is_bot:
            try:
                # Kick the bot from the group
                await context.bot.ban_chat_member(chat_id, new_member.id)
                await context.bot.unban_chat_member(chat_id, new_member.id)
                
                logging.info(
                    f"Bot Protection: Kicked bot @{new_member.username} ({new_member.id}) "
                    f"added by user {update.effective_user.id} in chat {chat_id}"
                )
                
                # Send notification message
                added_by = update.effective_user
                notification = (
                    f"🛡️ <b>Bot Protection</b>\n\n"
                    f"Bot <b>{new_member.mention_html()}</b> has been automatically removed.\n"
                    f"Added by: {added_by.mention_html()}\n\n"
                    f"<i>Bot protection is enabled. Bots cannot be added to this group.</i>"
                )
                
                await update.message.reply_text(notification, parse_mode='HTML')
                return True
                
            except Exception as e:
                logging.error(f"Bot Protection: Error kicking bot {new_member.id}: {e}")
                return False
    
    return False


async def bot_protection_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command to toggle bot protection on/off.
    Usage: /botprotection
    """
    if not update.effective_chat or update.effective_chat.type == "private":
        await update.message.reply_text("This command can only be used in groups!")
        return

    chat_id = update.effective_chat.id
    
    # Ensure chat settings are loaded
    if chat_id not in group_settings:
        group_settings[chat_id] = copy.deepcopy(DEFAULT_SETTINGS)
    
    # Check if user is admin
    member = await context.bot.get_chat_member(chat_id, update.effective_user.id)
    if member.status not in ["administrator", "creator"]:
        await update.message.reply_text("Only admins can use this command!")
        return

    # Toggle bot protection
    current_status = group_settings[chat_id].get("bot_protection_enabled", False)
    new_status = not current_status
    
    group_settings[chat_id]["bot_protection_enabled"] = new_status
    await save_settings(chat_id)
    
    status_text = "✅ enabled" if new_status else "❌ disabled"
    
    await update.message.reply_text(
        f"🛡️ <b>Bot Protection</b>\n\n"
        f"Bot protection has been {status_text}.\n\n"
        f"<i>When enabled, any bot added to this group will be automatically kicked.</i>",
        parse_mode='HTML'
    )

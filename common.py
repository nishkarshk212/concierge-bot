import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import group_settings, DEFAULT_SETTINGS
from font import apply_font

# Version Info
BOT_VERSION = "2.0.0 (Stable)"

# Premium Emoji IDs
EMOJI_STAR = "5431441851994156157" 
EMOJI_GEAR = "5328223749693910299"

def get_premium_emoji(emoji_id, fallback):
    return f"<tg-emoji emoji-id='{emoji_id}'>{fallback}</tg-emoji>"

# Conversation states for settings
SET_WELCOME_TEXT, SET_WELCOME_MEDIA, ADD_WELCOME_BUTTON_LABEL, ADD_WELCOME_BUTTON_URL, ADD_CUSTOM_BLOCK, SET_MSG_MIN, SET_MSG_MAX, SET_WELCOME_AUTODEL, SET_RULES_TEXT, SET_FLOOD_MSGS, SET_FLOOD_TIME, SET_GROUP_LINK = range(12)

async def check_permission(update: Update, context: ContextTypes.DEFAULT_TYPE, cmd_name: str) -> bool:
    """Checks if the user has permission to use a specific command."""
    if not update.effective_chat:
        return False
        
    chat_id = update.effective_chat.id
    is_private = update.effective_chat.type == "private"
    user_id = update.effective_user.id
    
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    cmd_perms = settings.get("cmd_perms", DEFAULT_SETTINGS["cmd_perms"])
    perm_level = cmd_perms.get(cmd_name, 2)
    
    if perm_level == 0:
        return False
        
    if perm_level == 3:
        return is_private
        
    if is_private:
        return True
        
    if perm_level == 1:
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            return member.status in ["administrator", "creator"]
        except Exception:
            return False
            
    return True

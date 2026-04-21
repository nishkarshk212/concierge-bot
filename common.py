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
SET_WELCOME_TEXT, SET_WELCOME_MEDIA, ADD_WELCOME_BUTTON_LABEL, ADD_WELCOME_BUTTON_URL, ADD_CUSTOM_BLOCK, SET_MSG_MIN, SET_MSG_MAX, SET_WELCOME_AUTODEL, SET_RULES_TEXT, SET_FLOOD_MSGS, SET_FLOOD_TIME, SET_GROUP_LINK, SET_RECURRING_TEXT, SET_RECURRING_MEDIA, ADD_RECURRING_BUTTON_LABEL, ADD_RECURRING_BUTTON_URL, ADD_CUSTOM_BLOCK_MEDIA, ADD_CUSTOM_BLOCK_STICKER = range(18)

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

async def check_admin_permissions(update: Update, context: ContextTypes.DEFAULT_TYPE, required_perms: list) -> tuple:
    """
    Check if admin user has required Telegram admin permissions.
    Supports both regular admins and anonymous admins.
    
    Args:
        update: Update object
        context: Context object  
        required_perms: List of required permissions (e.g., ['can_change_info', 'can_restrict_members'])
    
    Returns:
        tuple: (has_permission: bool, error_message: str)
    """
    if not update.effective_chat or update.effective_chat.type == "private":
        return False, "Please use this command in a group!"
    
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        
        # Creator has all permissions
        if member.status == "creator":
            return True, ""
        
        # Check if user is admin
        if member.status != "administrator":
            return False, "⚠️ Only admins can use this command!"
        
        # Check if admin is anonymous
        is_anonymous = member.user.is_anonymous
        
        if is_anonymous:
            # Use anonymous admin permission checker
            from anonymous_admin import check_anonymous_admin_permissions
            has_perm, error_msg, _ = await check_anonymous_admin_permissions(
                update, context, required_perms
            )
            return has_perm, error_msg
        
        # Regular admin - check Telegram permissions directly
        missing_perms = []
        
        for perm in required_perms:
            perm_value = getattr(member, perm, False)
            if not perm_value:
                missing_perms.append(perm)
        
        if missing_perms:
            # Format permission names for display
            perm_display_names = {
                'can_change_info': 'Change Group Info',
                'can_restrict_members': 'Ban Users',
                'can_delete_messages': 'Delete Messages',
                'can_invite_users': 'Add Members',
                'can_pin_messages': 'Pin Messages',
                'can_promote_members': 'Add New Admins'
            }
            
            missing_display = [perm_display_names.get(p, p) for p in missing_perms]
            error_msg = f"⚠️ You don't have required permissions:\n" + "\n".join([f"• {name}" for name in missing_display])
            return False, error_msg
        
        return True, ""
        
    except Exception as e:
        return False, f"❌ Error checking permissions: {str(e)}"

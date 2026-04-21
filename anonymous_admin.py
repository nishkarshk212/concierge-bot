"""
Anonymous Admin Handler
Manages permission checks for anonymous administrators.
Anonymous admins can use commands if they have the required Telegram permissions
and the feature is enabled in settings.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import group_settings, DEFAULT_SETTINGS


async def check_anonymous_admin_permissions(update: Update, context: ContextTypes.DEFAULT_TYPE, required_perms: list, bypass_enabled_check: bool = False) -> tuple:
    """
    Check if an anonymous admin has the required permissions to execute a command.
    
    Args:
        update: Update object
        context: Context object
        required_perms: List of required permissions
        bypass_enabled_check: If True, skips the check if anonymous admin feature is enabled in settings.
                             Used for initial bot setup.
    
    Returns:
        tuple: (has_permission: bool, error_message: str, is_anonymous: bool)
    """
    if not update.effective_chat or update.effective_chat.type == "private":
        return False, "Please use this command in a group!", False
    
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        
        # Creator has all permissions (not anonymous check needed)
        if member.status == "creator":
            return True, "", False
        
        # Check if user is admin
        if member.status != "administrator":
            return False, "⚠️ Only admins can use this command!", False
        
        # Check if this is an anonymous admin (ID 1087968824 is the anonymous bot)
        is_anonymous = user_id == 1087968824
        
        if not is_anonymous:
            # Not an anonymous admin, return False to let normal checks handle it
            return False, "", False
        
        # This is an anonymous admin - check if anonymous admin feature is enabled
        settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
        anon_enabled = settings.get("anon_admin_enabled", False)
        
        if not anon_enabled and not bypass_enabled_check:
            return False, "⚠️ Anonymous admin commands are disabled. Please enable anonymous admin support in settings.", True
        
        # If bypassed, and no specific permissions set yet, allow if they are an admin in Telegram
        if bypass_enabled_check:
            # For settings access, if it's the first time, allow any anonymous admin to open it
            # so they can at least enable the feature.
            return True, "", True

        # Get anonymous admin permissions from settings
        anon_perms = settings.get("anon_admin_perms", DEFAULT_SETTINGS.get("anon_admin_perms", {}))
        
        # Map Telegram permissions to our anonymous admin permission keys
        perm_mapping = {
            'can_change_info': 'add_admin',  # Change info maps to add_admin permission
            'can_restrict_members': 'ban',   # Ban/Restrict/Mute maps to ban permission
            'can_delete_messages': 'delete', # Delete messages maps to delete permission
            'can_pin_messages': 'pin',       # Pin messages maps to pin permission
            'can_promote_members': 'add_admin',  # Promote/demote maps to add_admin permission
        }
        
        # Check if anonymous admin has ALL required permissions
        missing_perms = []
        for required_perm in required_perms:
            anon_perm_key = perm_mapping.get(required_perm)
            if anon_perm_key and not anon_perms.get(anon_perm_key, False):
                # Get display name for the permission
                perm_display_names = {
                    'can_change_info': 'Change Group Info',
                    'can_restrict_members': 'Ban/Mute Users',
                    'can_delete_messages': 'Delete Messages',
                    'can_pin_messages': 'Pin Messages',
                    'can_promote_members': 'Add/Remove Admins'
                }
                missing_perms.append(perm_display_names.get(required_perm, required_perm))
            elif not anon_perm_key:
                # Permission not mapped - log warning
                logging.warning(f"Permission {required_perm} not mapped in anonymous admin perm_mapping")
        
        if missing_perms:
            error_msg = (
                f"⚠️ Anonymous admin doesn't have required permissions:\n" + 
                "\n".join([f"• {name}" for name in missing_perms]) +
                "\n\nPlease enable these permissions in Anonymous Admin settings."
            )
            return False, error_msg, True
        
        # Anonymous admin has all required permissions
        logging.info(f"Anonymous admin {user_id} authorized for action requiring {required_perms}")
        return True, "", True
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error checking anonymous admin permissions: {error_msg}")
        return False, f"❌ Error checking permissions: {error_msg}", False


async def can_anonymous_admin_ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> tuple:
    """Check if anonymous admin can ban/unban/mute users."""
    return await check_anonymous_admin_permissions(
        update, context,
        required_perms=['can_restrict_members']
    )


async def can_anonymous_admin_change_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> tuple:
    """Check if anonymous admin can change settings."""
    return await check_anonymous_admin_permissions(
        update, context,
        required_perms=['can_change_info', 'can_restrict_members']
    )


async def can_anonymous_admin_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> tuple:
    """Check if anonymous admin can delete messages."""
    return await check_anonymous_admin_permissions(
        update, context,
        required_perms=['can_delete_messages']
    )


async def can_anonymous_admin_pin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> tuple:
    """Check if anonymous admin can pin messages."""
    return await check_anonymous_admin_permissions(
        update, context,
        required_perms=['can_pin_messages']
    )


async def can_anonymous_admin_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> tuple:
    """Check if anonymous admin can add/remove admins."""
    return await check_anonymous_admin_permissions(
        update, context,
        required_perms=['can_promote_members']
    )


async def can_anonymous_admin_change_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> tuple:
    """Check if anonymous admin can change group info."""
    return await check_anonymous_admin_permissions(
        update, context,
        required_perms=['can_change_info']
    )

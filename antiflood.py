"""
Anti-Flood Module
Detects and handles message flooding in groups.
"""

import logging
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from config import group_settings, DEFAULT_SETTINGS


# Store message timestamps for flood detection
# Format: {chat_id: {user_id: [timestamp1, timestamp2, ...]}}
flood_tracker = {}

# Store warning counts for users
# Format: {chat_id: {user_id: warning_count}}
warning_tracker = {}


async def check_antiflood(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Check if a user is flooding the chat and apply punishment.
    
    Returns:
        bool: True if message should be deleted/ignored, False otherwise
    """
    if not update.effective_chat or update.effective_chat.type == "private":
        return False
    
    if not update.message:
        return False
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Get settings
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    antiflood_enabled = settings.get("antiflood_punishment", "off") != "off"
    
    if not antiflood_enabled:
        return False
    
    max_messages = settings.get("antiflood_messages", 5)
    time_window = settings.get("antiflood_time", 3)
    punishment = settings.get("antiflood_punishment", "off")
    delete_message = settings.get("antiflood_delete", False)
    warn_limit = settings.get("antiflood_warn_limit", 3)
    
    # Initialize tracker for this chat if needed
    if chat_id not in flood_tracker:
        flood_tracker[chat_id] = {}
    
    if user_id not in flood_tracker[chat_id]:
        flood_tracker[chat_id][user_id] = []
    
    # Initialize warning tracker if needed
    if chat_id not in warning_tracker:
        warning_tracker[chat_id] = {}
    
    if user_id not in warning_tracker[chat_id]:
        warning_tracker[chat_id][user_id] = 0
    
    # Get current time
    now = datetime.now()
    
    # Remove old timestamps outside the time window
    cutoff_time = now - timedelta(seconds=time_window)
    flood_tracker[chat_id][user_id] = [
        ts for ts in flood_tracker[chat_id][user_id] 
        if ts > cutoff_time
    ]
    
    # Add current message timestamp
    flood_tracker[chat_id][user_id].append(now)
    
    # Check if user exceeded the limit
    message_count = len(flood_tracker[chat_id][user_id])
    
    if message_count > max_messages:
        # Increment warning count
        warning_tracker[chat_id][user_id] += 1
        current_warnings = warning_tracker[chat_id][user_id]
        
        logging.info(
            f"ANTIFLOOD: User {user_id} sent {message_count} messages in {time_window}s "
            f"(limit: {max_messages}) - Warning {current_warnings}/{warn_limit} in chat {chat_id}"
        )
        
        # Delete the message if configured
        if delete_message:
            try:
                await update.message.delete()
                logging.info(f"ANTIFLOOD: Deleted flood message from user {user_id}")
            except Exception as e:
                logging.error(f"ANTIFLOOD: Failed to delete message: {e}")
        
        # Check if warning limit reached
        if current_warnings >= warn_limit:
            # Apply punishment
            logging.info(
                f"ANTIFLOOD: User {user_id} reached warning limit ({current_warnings}/{warn_limit}), "
                f"applying {punishment} punishment"
            )
            
            if punishment == "warn":
                await _warn_user(context, chat_id, user_id, current_warnings, warn_limit)
            elif punishment == "mute":
                await _mute_user(context, chat_id, user_id, time_window)
            elif punishment == "ban":
                await _ban_user(context, chat_id, user_id)
            elif punishment == "kick":
                await _kick_user(context, chat_id, user_id)
            
            # Reset warnings after punishment
            warning_tracker[chat_id][user_id] = 0
        else:
            # Send warning message
            await _send_warning(context, chat_id, user_id, current_warnings, warn_limit)
        
        # Reset the message tracker for this user
        flood_tracker[chat_id][user_id] = []
        
        return delete_message
    
    return False


async def _mute_user(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, duration: int):
    """Mute user for the flood time window duration."""
    try:
        from datetime import timedelta
        until_date = datetime.now() + timedelta(seconds=duration)
        
        await context.bot.restrict_chat_member(
            chat_id,
            user_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        
        logging.info(f"ANTIFLOOD: Muted user {user_id} for {duration} seconds")
        
        # Send notification
        try:
            await context.bot.send_message(
                chat_id,
                f"⚠️ User {user_id} has been muted for flooding!",
                parse_mode='HTML'
            )
        except Exception:
            pass
            
    except Exception as e:
        logging.error(f"ANTIFLOOD: Failed to mute user {user_id}: {e}")


async def _ban_user(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int):
    """Ban user from the chat."""
    try:
        await context.bot.ban_chat_member(chat_id, user_id)
        logging.info(f"ANTIFLOOD: Banned user {user_id}")
        
        # Send notification
        try:
            await context.bot.send_message(
                chat_id,
                f"🚫 User {user_id} has been banned for flooding!",
                parse_mode='HTML'
            )
        except Exception:
            pass
            
    except Exception as e:
        logging.error(f"ANTIFLOOD: Failed to ban user {user_id}: {e}")


async def _kick_user(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int):
    """Kick user from the chat."""
    try:
        await context.bot.ban_chat_member(chat_id, user_id)
        await context.bot.unban_chat_member(chat_id, user_id)
        logging.info(f"ANTIFLOOD: Kicked user {user_id}")
        
        # Send notification
        try:
            await context.bot.send_message(
                chat_id,
                f"👢 User {user_id} has been kicked for flooding!",
                parse_mode='HTML'
            )
        except Exception:
            pass
            
    except Exception as e:
        logging.error(f"ANTIFLOOD: Failed to kick user {user_id}: {e}")


async def _warn_user(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, current_warnings: int, warn_limit: int):
    """Send final warning before punishment (when punishment is 'warn')."""
    try:
        await context.bot.send_message(
            chat_id,
            f"⚠️ <b>Anti-Flood Warning!</b>\n\n"
            f"User {user_id} has received {current_warnings} warnings for flooding.\n"
            f"This is your final warning. Further violations will result in punishment!",
            parse_mode='HTML'
        )
        logging.info(f"ANTIFLOOD: Sent final warning to user {user_id} ({current_warnings}/{warn_limit})")
    except Exception as e:
        logging.error(f"ANTIFLOOD: Failed to warn user {user_id}: {e}")


async def _send_warning(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, current_warnings: int, warn_limit: int):
    """Send warning message to user."""
    try:
        remaining = warn_limit - current_warnings
        await context.bot.send_message(
            chat_id,
            f"⚠️ <b>Anti-Flood Warning!</b>\n\n"
            f"User {user_id}, you are sending messages too quickly!\n"
            f"Warning {current_warnings}/{warn_limit}\n"
            f"{remaining} more warning(s) before punishment.",
            parse_mode='HTML'
        )
        logging.info(f"ANTIFLOOD: Sent warning {current_warnings}/{warn_limit} to user {user_id}")
    except Exception as e:
        logging.error(f"ANTIFLOOD: Failed to send warning to user {user_id}: {e}")


def cleanup_flood_tracker():
    """Clean up old entries from flood tracker and warning tracker to prevent memory leaks."""
    now = datetime.now()
    cutoff_time = now - timedelta(minutes=5)
    
    # Clean flood tracker
    chats_to_remove = []
    for chat_id, users in flood_tracker.items():
        users_to_remove = []
        for user_id, timestamps in users.items():
            # Remove old timestamps
            users[user_id] = [ts for ts in timestamps if ts > cutoff_time]
            # Mark empty user entries for removal
            if not users[user_id]:
                users_to_remove.append(user_id)
        
        # Remove empty user entries
        for user_id in users_to_remove:
            del users[user_id]
        
        # Mark empty chat entries for removal
        if not users:
            chats_to_remove.append(chat_id)
    
    # Remove empty chat entries
    for chat_id in chats_to_remove:
        del flood_tracker[chat_id]
    
    if chats_to_remove:
        logging.info(f"ANTIFLOOD: Cleaned up {len(chats_to_remove)} empty chat entries from flood tracker")
    
    # Clean warning tracker (reset warnings older than 5 minutes)
    warn_chats_to_remove = []
    for chat_id, users in warning_tracker.items():
        # Keep only users with warnings (we'll reset them if they're inactive)
        users_to_remove = []
        for user_id, warn_count in users.items():
            # If user has no recent messages, reset their warnings
            if chat_id in flood_tracker and user_id in flood_tracker[chat_id]:
                if not flood_tracker[chat_id][user_id]:
                    users_to_remove.append(user_id)
            else:
                users_to_remove.append(user_id)
        
        # Remove inactive user entries
        for user_id in users_to_remove:
            del users[user_id]
        
        # Mark empty chat entries for removal
        if not users:
            warn_chats_to_remove.append(chat_id)
    
    # Remove empty chat entries
    for chat_id in warn_chats_to_remove:
        del warning_tracker[chat_id]
    
    if warn_chats_to_remove:
        logging.info(f"ANTIFLOOD: Cleaned up {len(warn_chats_to_remove)} empty chat entries from warning tracker")

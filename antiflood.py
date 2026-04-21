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
    
    # Initialize tracker for this chat if needed
    if chat_id not in flood_tracker:
        flood_tracker[chat_id] = {}
    
    if user_id not in flood_tracker[chat_id]:
        flood_tracker[chat_id][user_id] = []
    
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
        logging.info(
            f"ANTIFLOOD: User {user_id} sent {message_count} messages in {time_window}s "
            f"(limit: {max_messages}) in chat {chat_id}"
        )
        
        # Delete the message if configured
        if delete_message:
            try:
                await update.message.delete()
                logging.info(f"ANTIFLOOD: Deleted flood message from user {user_id}")
            except Exception as e:
                logging.error(f"ANTIFLOOD: Failed to delete message: {e}")
        
        # Apply punishment
        if punishment == "mute":
            await _mute_user(context, chat_id, user_id, time_window)
        elif punishment == "ban":
            await _ban_user(context, chat_id, user_id)
        elif punishment == "kick":
            await _kick_user(context, chat_id, user_id)
        
        # Reset the tracker for this user
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


def cleanup_flood_tracker():
    """Clean up old entries from flood tracker to prevent memory leaks."""
    now = datetime.now()
    cutoff_time = now - timedelta(minutes=5)
    
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
        logging.info(f"ANTIFLOOD: Cleaned up {len(chats_to_remove)} empty chat entries from tracker")

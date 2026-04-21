"""
Manual welcome command for testing welcome messages.
Usage: /welcometest @username or /welcometest user_id or reply to a user
"""
from telegram import Update
from telegram.ext import ContextTypes
from database import get_chat_settings
from welcome_feature import preview_welcome
from common import apply_font
import logging

async def test_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually trigger welcome message for testing."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    logging.info(f"[TEST-WELCOME] Command triggered by user {user.id} ({user.first_name}) in chat {chat_id}")
    
    # Check if user is admin
    admins = await context.bot.get_chat_administrators(chat_id)
    admin_ids = [admin.user.id for admin in admins]
    
    if user.id not in admin_ids and user.id != 1087968824:  # 1087968824 is anonymous admin
        logging.info(f"[TEST-WELCOME] User {user.id} is not admin - command rejected")
        await update.message.reply_text(apply_font("❌ Only admins can use this command!"))
        return
    
    logging.info(f"[TEST-WELCOME] User {user.id} is admin - proceeding")
    
    # Parse the target user
    if context.args:
        target_arg = context.args[0]
        logging.info(f"[TEST-WELCOME] Target argument: {target_arg}")
        
        # Check if it's a user ID
        if target_arg.isdigit():
            target_user_id = int(target_arg)
            # Create a minimal User object since we can't get full user info
            from telegram import User
            target_user = User(
                id=target_user_id,
                is_bot=False,
                first_name=f"User{target_user_id}",
                last_name=None,
                username=None,
                language_code=None
            )
            logging.info(f"[TEST-WELCOME] Created User object for ID: {target_user_id}")
        # Check if it's a mention
        elif target_arg.startswith('@'):
            username = target_arg[1:]  # Remove @
            logging.info(f"[TEST-WELCOME] Username provided: {username}")
            try:
                # Try to get user by username (this won't work for most users)
                await update.message.reply_text(apply_font("⚠️ Please use user ID instead of username.\n\nTo get user ID:\n1. Add @userinfobot to the group\n2. Reply to their message with /id"))
                return
            except:
                await update.message.reply_text(apply_font("❌ User not found!"))
                return
        else:
            logging.info(f"[TEST-WELCOME] Invalid format: {target_arg}")
            await update.message.reply_text(apply_font("❌ Invalid format. Use:\n/welcometest <user_id>\nExample: /welcometest 8778115783"))
            return
    elif update.message.reply_to_message:
        # Use replied user
        target_user = update.message.reply_to_message.from_user
        logging.info(f"[TEST-WELCOME] Using replied user: {target_user.id} ({target_user.first_name})")
    else:
        logging.info(f"[TEST-WELCOME] No target specified, showing help")
        await update.message.reply_text(apply_font("❌ Please specify a user:\n/welcometest <user_id>\nOR reply to their message with /welcometest"))
        return
    
    # Check if welcome is enabled
    settings = await get_chat_settings(chat_id)
    logging.info(f"[TEST-WELCOME] Chat settings loaded: welcome_enabled={settings.get('welcome_enabled')}")
    
    if not settings.get("welcome_enabled"):
        logging.info(f"[TEST-WELCOME] Welcome is not enabled in chat {chat_id}")
        await update.message.reply_text(apply_font("❌ Welcome is not enabled in this group!\n\nEnable it via /settings → Welcome → Status"))
        return
    
    # Send welcome
    logging.info(f"[TEST-WELCOME] Sending test welcome for user {target_user.first_name} (ID: {target_user.id})")
    await update.message.reply_text(apply_font(f"🔧 Testing welcome for user {target_user.first_name} (ID: {target_user.id})..."))
    
    try:
        await preview_welcome(update, context, chat_id, target_user=target_user)
        logging.info(f"[TEST-WELCOME] ✓ Welcome message sent successfully for user {target_user.id}")
        await update.message.reply_text(apply_font("✅ Welcome message sent successfully!"))
    except Exception as e:
        logging.error(f"[TEST-WELCOME] ✗ Error sending welcome: {e}", exc_info=True)
        await update.message.reply_text(apply_font(f"❌ Failed to send welcome: {str(e)}"))


async def welcometest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Alias for test_welcome - /welcometest command."""
    await test_welcome(update, context)

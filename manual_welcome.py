"""
Manual welcome command for testing welcome messages.
Usage: /testwelcome @username or /testwelcome user_id
"""
from telegram import Update
from telegram.ext import ContextTypes
from database import get_chat_settings
from welcome_feature import preview_welcome
from common import apply_font

async def test_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually trigger welcome message for testing."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # Check if user is admin
    admins = await context.bot.get_chat_administrators(chat_id)
    admin_ids = [admin.user.id for admin in admins]
    
    if user.id not in admin_ids and user.id != 1087968824:  # 1087968824 is anonymous admin
        await update.message.reply_text(apply_font("❌ Only admins can use this command!"))
        return
    
    # Parse the target user
    if context.args:
        target_arg = context.args[0]
        
        # Check if it's a user ID
        if target_arg.isdigit():
            target_user_id = int(target_arg)
            try:
                target_user = await context.bot.get_chat(target_user_id)
            except Exception as e:
                await update.message.reply_text(apply_font(f"❌ Could not find user: {str(e)}"))
                return
        # Check if it's a mention
        elif target_arg.startswith('@'):
            username = target_arg[1:]  # Remove @
            try:
                # Try to get user by username (this won't work for most users)
                await update.message.reply_text(apply_font("⚠️ Please use user ID instead of username.\n\nTo get user ID:\n1. Add @userinfobot to the group\n2. Reply to their message with /id"))
                return
            except:
                await update.message.reply_text(apply_font("❌ User not found!"))
                return
        else:
            await update.message.reply_text(apply_font("❌ Invalid format. Use:\n/testwelcome <user_id>\nExample: /testwelcome 8778115783"))
            return
    elif update.message.reply_to_message:
        # Use replied user
        target_user = update.message.reply_to_message.from_user
    else:
        await update.message.reply_text(apply_font("❌ Please specify a user:\n/testwelcome <user_id>\nOR reply to their message with /testwelcome"))
        return
    
    # Check if welcome is enabled
    settings = await get_chat_settings(chat_id)
    if not settings.get("welcome_enabled"):
        await update.message.reply_text(apply_font("❌ Welcome is not enabled in this group!\n\nEnable it via /settings → Welcome → Status"))
        return
    
    # Send welcome
    await update.message.reply_text(apply_font(f"🔧 Testing welcome for user {target_user.first_name} (ID: {target_user.id})..."))
    
    try:
        await preview_welcome(update, context, chat_id, target_user=target_user)
        await update.message.reply_text(apply_font("✅ Welcome message sent successfully!"))
    except Exception as e:
        await update.message.reply_text(apply_font(f"❌ Failed to send welcome: {str(e)}"))
        import logging
        logging.error(f"[TEST-WELCOME] Error: {e}", exc_info=True)

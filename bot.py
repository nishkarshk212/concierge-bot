import logging
import copy
import asyncio
from datetime import datetime
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, ConversationHandler, ChatMemberHandler
from telegram import BotCommand, Update
from telegram.error import RetryAfter

from config import BOT_TOKEN, group_settings, DEFAULT_SETTINGS, LOG_GROUP_ID
from update_notifier import send_startup_with_updates
from database import load_all_settings, save_settings, get_chat_settings
from common import check_permission
from blocking import handle_blocking, handle_clean_service
from bot_protection import handle_bot_protection, bot_protection_command
from self_destruction import schedule_self_destruction
from antiflood import check_antiflood

# Import feature modules
from filters_feature import filter_command, filters_command, stop_command, stopall_command, handle_filters
from reports_feature import report_command, handle_reports_trigger
from welcome_feature import (
    set_welcome_text_handler, set_welcome_media_handler, 
    add_welcome_button_label_handler, add_welcome_button_url_handler,
    set_welcome_autodel_handler
)
from admin_feature import (
    info_command, staff_command, free_command, admin_command, unadmin_command, 
    unfree_command, reload_command, unmute_command, unban_command,
    ban_command, mute_command, warn_command, cban_command, block_command, unblock_command
)
from other_features import (
    start, rules_command, me_command, translate_command, link_command, 
    help_command, settings_command, on_my_chat_member_update, extract_emoji_pack
)
from manual_welcome import test_welcome
from callback_handler import (
    button_callback, set_rules_text_handler, add_custom_block_handler,
    set_msg_min_handler, set_msg_max_handler, set_flood_msgs_handler,
    set_flood_time_handler, set_group_link_handler, add_custom_block_media_handler,
    add_custom_block_sticker_handler,
    # Entry point handlers for ConversationHandlers (prevent double-processing)
    entry_set_msg_min, entry_set_msg_max, entry_set_rules_text, entry_set_group_link,
    entry_set_welcome_text, entry_set_welcome_media, entry_set_welcome_autodel,
    entry_add_welcome_button,
    entry_add_custom_block, entry_add_custom_block_media, entry_add_custom_block_sticker,
    entry_set_flood_msgs, entry_set_flood_time,
    entry_set_recurring_text, entry_set_recurring_media,
    entry_add_recurring_button
)
from welcome_feature import (
    set_welcome_text_handler, set_welcome_media_handler, 
    add_welcome_button_label_handler, add_welcome_button_url_handler,
    set_welcome_autodel_handler
)
from recurring_messages import (
    set_recurring_text_handler, set_recurring_media_handler,
    add_recurring_button_label_handler, add_recurring_button_url_handler
)
from common import (
    SET_WELCOME_TEXT, SET_WELCOME_MEDIA, ADD_WELCOME_BUTTON_LABEL, ADD_WELCOME_BUTTON_URL, 
    ADD_CUSTOM_BLOCK, SET_MSG_MIN, SET_MSG_MAX, SET_WELCOME_AUTODEL, SET_RULES_TEXT, 
    SET_FLOOD_MSGS, SET_FLOOD_TIME, SET_GROUP_LINK, SET_RECURRING_TEXT, SET_RECURRING_MEDIA,
    ADD_RECURRING_BUTTON_LABEL, ADD_RECURRING_BUTTON_URL, ADD_CUSTOM_BLOCK_MEDIA, ADD_CUSTOM_BLOCK_STICKER
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def pre_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pre-handler that runs for ALL messages including commands."""
    if not update.effective_chat or update.effective_chat.type == "private":
        return
    
    chat_id = update.effective_chat.id
    logging.info(f"[PRE_HANDLER] Message in chat {chat_id}, type={update.effective_chat.type}, has_sticker={bool(update.message and update.message.sticker)}")
    
    # Ensure chat settings are loaded
    if chat_id not in group_settings:
        group_settings[chat_id] = copy.deepcopy(DEFAULT_SETTINGS)
    
    # Get fresh settings from MongoDB for self-destruction
    settings = await get_chat_settings(chat_id)
    
    # Handle self-destruction for ALL messages
    await schedule_self_destruction(update, context, settings)

async def on_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle chat member updates (join/leave) - Welcome enabled."""
    logging.info(f"[CHAT_MEMBER_DEBUG] Received update: {update}")
    if not update.chat_member:
        logging.info("[CHAT_MEMBER_DEBUG] No chat_member in update, skipping")
        return
    
    chat_id = update.chat_member.chat.id
    status_before = update.chat_member.old_chat_member.status
    status_after = update.chat_member.new_chat_member.status
    user = update.chat_member.new_chat_member.user
    
    logging.info(f"[CHAT_MEMBER_DEBUG] User {user.id} ({user.first_name}) status: {status_before} -> {status_after}")
    
    # Check if a user joined (was not a member, now is)
    is_join = False
    if status_before in ['left', 'kicked'] and status_after in ['member', 'administrator', 'creator']:
        is_join = True
    elif status_before == 'member' and status_after == 'administrator':
        # Just a promotion, not a new join
        logging.info(f"[CHAT_MEMBER_DEBUG] User promoted, not a new join")
        pass
        
    if is_join:
        logging.info(f"[CHAT_MEMBER] User {user.id} ({user.first_name}) joined chat {chat_id}")
        settings = await get_chat_settings(chat_id)
        
        if user.is_bot:
            # If the bot itself joined, the start command is handled by on_my_chat_member_update
            logging.info(f"[CHAT_MEMBER] Bot joined, skipping welcome")
            return
            
        if settings.get("welcome_enabled"):
            logging.info(f"[WELCOME] Welcome enabled, sending message for user {user.id}")
            from welcome_feature import preview_welcome
            
            # Check if this is a rejoining user
            is_rejoining_user = False
            if "seen_users" not in group_settings[chat_id]:
                group_settings[chat_id]["seen_users"] = []
            
            if user.id in group_settings[chat_id]["seen_users"]:
                is_rejoining_user = True
                logging.info(f"[WELCOME] User {user.id} is a REJOINING user")
            
            # Check if we should welcome rejoining users
            welcome_rejoin = settings.get("welcome_rejoin", False)
            
            if is_rejoining_user and not welcome_rejoin:
                # User is rejoining but rejoin welcome is disabled - skip welcome
                logging.info(f"[WELCOME] User {user.id} is rejoining but welcome_rejoin is disabled - skipping")
                return
            
            # Mark user as seen (if not already)
            if user.id not in group_settings[chat_id]["seen_users"]:
                group_settings[chat_id]["seen_users"].append(user.id)
                await save_settings(chat_id)
                logging.info(f"[WELCOME] User {user.id} marked as seen BEFORE sending welcome")
            
            # Now send the welcome
            try:
                await preview_welcome(update, context, chat_id, target_user=user)
                logging.info(f"[WELCOME] Welcome message sent successfully")
            except Exception as e:
                logging.error(f"[WELCOME] Failed to send welcome: {e}", exc_info=True)
        else:
            logging.info(f"[WELCOME] Welcome not enabled for chat {chat_id}")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat:
        return
    
    chat_id = update.effective_chat.id
    logging.info(f"[MESSAGE_HANDLER] Received message in chat {chat_id}, has_sticker={bool(update.message and update.message.sticker)}, has_text={bool(update.message and update.message.text)}")
    
    settings = await get_chat_settings(chat_id)
    
    # Check if it's a service message first (for cleaning)
    if update.message and (update.message.new_chat_members or update.message.left_chat_member):
        if update.message.new_chat_members:
            bot_id = context.bot.id
            for member in update.message.new_chat_members:
                if member.id == bot_id:
                    # Bot added - show thank you
                    from other_features import start
                    await start(update, context) # Re-use start logic for welcome
                    return
                else:
                    # User joined via service message - Send welcome
                    if settings.get("welcome_enabled"):
                        logging.info(f"[WELCOME] User {member.id} ({member.first_name}) joined via service message in chat {chat_id}")
                        from welcome_feature import preview_welcome
                        
                        # Check if this is a rejoining user
                        is_rejoining_user = False
                        if "seen_users" not in group_settings[chat_id]:
                            group_settings[chat_id]["seen_users"] = []
                        
                        if member.id in group_settings[chat_id]["seen_users"]:
                            is_rejoining_user = True
                            logging.info(f"[WELCOME] User {member.id} is a REJOINING user (service message)")
                        
                        # Check if we should welcome rejoining users
                        welcome_rejoin = settings.get("welcome_rejoin", False)
                        
                        if is_rejoining_user and not welcome_rejoin:
                            # User is rejoining but rejoin welcome is disabled - skip welcome
                            logging.info(f"[WELCOME] User {member.id} is rejoining but welcome_rejoin is disabled - skipping")
                        else:
                            # Mark user as seen (if not already)
                            if member.id not in group_settings[chat_id]["seen_users"]:
                                group_settings[chat_id]["seen_users"].append(member.id)
                                await save_settings(chat_id)
                                logging.info(f"[WELCOME] User {member.id} marked as seen BEFORE sending welcome")
                            
                            try:
                                await preview_welcome(update, context, chat_id, target_user=member)
                                logging.info(f"[WELCOME] Welcome sent successfully to user {member.id}")
                            except Exception as e:
                                logging.error(f"[WELCOME] Failed to send welcome: {e}", exc_info=True)
        
        if update.message.left_chat_member:
            # If any user freed then user left then user unfree if rejoin user not be freed
            left_user_id = str(update.message.left_chat_member.id)
            if "user_roles" in settings and left_user_id in settings["user_roles"]:
                if settings["user_roles"][left_user_id].get("is_free"):
                    settings["user_roles"][left_user_id]["is_free"] = False
                    await save_settings(chat_id)
                    logging.info(f"User {left_user_id} was freed but left the group. Unfreed.")

    # Check for premium emoji extraction
    if update.effective_chat.type == "private" and update.message:
        from telegram import MessageEntity
        if any(e.type == MessageEntity.CUSTOM_EMOJI for e in (update.message.entities or [])):
            await extract_emoji_pack(update, context)
            return

    # Check if it's a service message first (for cleaning)
    if await handle_clean_service(update, context):
        return

    # Check bot protection (kick bots when added)
    if await handle_bot_protection(update, context):
        return

    # Check blocking rules (includes command blocking)
    deleted = await handle_blocking(update, context)
    if deleted:
        return

    # Check anti-flood
    flood_deleted = await check_antiflood(update, context)
    if flood_deleted:
        return

    # Check for @admin trigger
    if await handle_reports_trigger(update, context):
        return

    # Check for filters
    if await handle_filters(update, context, settings):
        return

async def weekly_cache_clear_job(context: ContextTypes.DEFAULT_TYPE):
    """Clears unnecessary in-memory data every week and notifies log group."""
    global group_settings
    
    # 1. Clear 'seen_users' cache for all groups to free up memory
    cleared_count = 0
    for chat_id in group_settings:
        if "seen_users" in group_settings[chat_id]:
            cleared_count += len(group_settings[chat_id]["seen_users"])
            group_settings[chat_id]["seen_users"] = []
            await save_settings(chat_id)
            
    # 2. Notify log group
    log_text = (
        f"🧹 <b>ᴡᴇᴇᴋʟʏ ᴄᴀᴄʜᴇ ᴄʟᴇᴀʀ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</b>\n\n"
        f"❅─────✧❅✦❅✧─────❅\n\n"
        f"🗑 <b>ᴄʟᴇᴀʀᴇᴅ ᴅᴀᴛᴀ:</b> {cleared_count} user entries\n"
        f"📅 <b>ɴᴇxᴛ ᴄʟᴇᴀʀ:</b> 7 days from now\n"
        f"🛡 <b>sᴛᴀᴛᴜs:</b> System Optimized"
    )
    try:
        await context.bot.send_message(LOG_GROUP_ID, log_text, parse_mode='HTML')
    except Exception as e:
        logging.error(f"Error sending weekly cache clear log: {e}")

async def error_handler(update, context):
    """Global error handler to catch and handle errors gracefully."""
    if isinstance(context.error, RetryAfter):
        # Rate limit hit - wait and retry
        retry_after = context.error.retry_after
        logging.warning(f"Rate limit hit! Waiting {retry_after} seconds before retry...")
        await asyncio.sleep(retry_after)
        return
    else:
        # Log other errors but don't crash
        logging.error(f"Update {update} caused error: {context.error}", exc_info=context.error)

async def post_init(application):
    """Sets the bot's commands and initializes database."""
    await load_all_settings()
    
    # Schedule weekly cache clear (7 days)
    application.job_queue.run_repeating(weekly_cache_clear_job, interval=604800, first=604800)
    
    # Define recent updates/features (update this list when deploying new features)
    recent_updates = [
        "✅ Free permission panel toggle buttons - green check (allowed), red cross (not allowed)",
        "✅ Save button stability in free permission panel - no longer changes to Back button",
        "✅ User-specific permission tracking in free command panel",
        "✅ Update notification system - logs all updates to log group with service name",
    ]
    
    # Send startup/update notification to log group
    try:
        await send_startup_with_updates(
            application.bot, 
            features_added=recent_updates,
            service_name="titanic-bot"
        )
    except Exception as e:
        logging.error(f"Error sending startup/update log: {e}")

    commands = [
        BotCommand("ban", "Ban a user [username/id/reply]"),
        BotCommand("cban", "Ban a channel [link/username/id]"),
        BotCommand("block", "Add word/text to block list"),
        BotCommand("unblock", "Remove word/text from block list"),
        BotCommand("mute", "Mute a user [username/id/reply]"),
        BotCommand("warn", "Warn a user [username/id/reply]"),
        BotCommand("unban", "Unban a user [username/id/reply]"),
        BotCommand("unmute", "Unmute a user [username/id/reply]"),
        BotCommand("unwarn", "Remove a warning [username/id/reply]"),
        BotCommand("free", "Make a user FREE from blocks"),
        BotCommand("unfree", "Remove user from FREE list"),
        BotCommand("admin", "Promote a user to Admin"),
        BotCommand("unadmin", "Demote an admin"),
        BotCommand("reload", "Update the admins list"),
        BotCommand("staff", "List group staff"),
        BotCommand("rules", "Show group rules"),
        BotCommand("me", "Show your information"),
        BotCommand("translate", "Translate replied message"),
        BotCommand("report", "Report a message to staff"),
        BotCommand("link", "Get group invite link"),
        BotCommand("filter", "Add a new filter"),
        BotCommand("filters", "List all filters"),
        BotCommand("stop", "Remove a filter"),
        BotCommand("stopall", "Remove all filters"),
        BotCommand("info", "Show bot information"),
        BotCommand("settings", "Manage bot settings"),
        BotCommand("help", "Get help and command list")
    ]
    await application.bot.set_my_commands(commands)

if __name__ == '__main__':
    
    application = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    
    # Register global error handler
    application.add_error_handler(error_handler)
    
    # Simple CallbackQueryHandler instead of ConversationHandler
    # Register at group=-1 (high priority) to ensure it processes callbacks before ConversationHandlers
    button_handler = CallbackQueryHandler(button_callback)
    application.add_handler(button_handler, group=-1)
    
    # Register handlers in proper order
    application.add_handler(ChatMemberHandler(on_chat_member_update, ChatMemberHandler.CHAT_MEMBER))
    application.add_handler(ChatMemberHandler(on_my_chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER))
    
    # Pre-handler for all messages
    application.add_handler(MessageHandler(filters.ALL, pre_message_handler), group=-3)
    
    # Add message handler FIRST (group -2) to process ALL messages for blocking/cleaning (including commands)
    # This ensures blocking logic runs before command handlers
    application.add_handler(MessageHandler(filters.ALL, message_handler), group=-2)
    
    # Command handlers (group -1, will only run if message wasn't deleted by blocking)
    application.add_handler(CommandHandler('start', start), group=-1)
    application.add_handler(CommandHandler('staff', staff_command), group=-1)
    application.add_handler(CommandHandler('rules', rules_command), group=-1)
    application.add_handler(CommandHandler('me', me_command), group=-1)
    application.add_handler(CommandHandler('translate', translate_command), group=-1)
    application.add_handler(CommandHandler('link', link_command), group=-1)
    application.add_handler(CommandHandler('report', report_command), group=-1)
    application.add_handler(CommandHandler('testwelcome', test_welcome), group=-1)
    application.add_handler(CommandHandler('filter', filter_command), group=-1)
    application.add_handler(CommandHandler('filters', filters_command), group=-1)
    application.add_handler(CommandHandler('stop', stop_command), group=-1)
    application.add_handler(CommandHandler('stopall', stopall_command), group=-1)
    application.add_handler(CommandHandler(['admin', 'promote'], admin_command), group=-1)
    application.add_handler(CommandHandler(['unadmin', 'demote'], unadmin_command), group=-1)
    application.add_handler(CommandHandler('free', free_command), group=-1)
    application.add_handler(CommandHandler('unfree', unfree_command), group=-1)
    application.add_handler(CommandHandler('reload', reload_command), group=-1)
    application.add_handler(CommandHandler('unmute', unmute_command), group=-1)
    application.add_handler(CommandHandler('unban', unban_command), group=-1)
    application.add_handler(CommandHandler('ban', ban_command), group=-1)
    application.add_handler(CommandHandler('cban', cban_command), group=-1)
    application.add_handler(CommandHandler('block', block_command), group=-1)
    application.add_handler(CommandHandler('unblock', unblock_command), group=-1)
    application.add_handler(CommandHandler('mute', mute_command), group=-1)
    application.add_handler(CommandHandler('warn', warn_command), group=-1)
    application.add_handler(CommandHandler('info', info_command), group=-1)
    application.add_handler(CommandHandler(['settings', 'config'], settings_command), group=-1)
    application.add_handler(CommandHandler('help', help_command), group=-1)
    application.add_handler(CommandHandler('botprotection', bot_protection_command), group=-1)
    
    # Register ConversationHandlers for settings that require user input
    # These handlers will intercept messages when user is in a setting state
    # Use group=1 to ensure they run after blocking (group=-2) but can still intercept when in conversation state
    
    # Message Length settings
    conv_msg_min = ConversationHandler(
        entry_points=[CallbackQueryHandler(entry_set_msg_min, pattern="^set_msg_min$")],
        states={
            SET_MSG_MIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_msg_min_handler)],
        },
        fallbacks=[],
        per_message=False,
    )
    application.add_handler(conv_msg_min, group=1)
    
    conv_msg_max = ConversationHandler(
        entry_points=[CallbackQueryHandler(entry_set_msg_max, pattern="^set_msg_max$")],
        states={
            SET_MSG_MAX: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_msg_max_handler)],
        },
        fallbacks=[],
        per_message=False,
    )
    application.add_handler(conv_msg_max, group=1)
    
    # Rules settings
    conv_rules = ConversationHandler(
        entry_points=[CallbackQueryHandler(entry_set_rules_text, pattern="^set_rules_text$")],
        states={
            SET_RULES_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_rules_text_handler)],
        },
        fallbacks=[],
        per_message=False,
    )
    application.add_handler(conv_rules, group=1)
    
    # Group Link settings
    conv_link = ConversationHandler(
        entry_points=[CallbackQueryHandler(entry_set_group_link, pattern="^set_group_link$")],
        states={
            SET_GROUP_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_group_link_handler)],
        },
        fallbacks=[],
        per_message=False,
    )
    application.add_handler(conv_link, group=1)
    
    # Welcome settings
    conv_welcome_text = ConversationHandler(
        entry_points=[CallbackQueryHandler(entry_set_welcome_text, pattern="^set_welcome_text$")],
        states={
            SET_WELCOME_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_welcome_text_handler)],
        },
        fallbacks=[],
        per_message=False,
    )
    application.add_handler(conv_welcome_text, group=1)
    
    conv_welcome_media = ConversationHandler(
        entry_points=[CallbackQueryHandler(entry_set_welcome_media, pattern="^set_welcome_media$")],
        states={
            SET_WELCOME_MEDIA: [MessageHandler(filters.ALL, set_welcome_media_handler)],
        },
        fallbacks=[],
        per_message=False,
    )
    application.add_handler(conv_welcome_media, group=1)
    
    conv_welcome_autodel = ConversationHandler(
        entry_points=[CallbackQueryHandler(entry_set_welcome_autodel, pattern="^set_welcome_autodel$")],
        states={
            SET_WELCOME_AUTODEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_welcome_autodel_handler)],
        },
        fallbacks=[],
        per_message=False,
    )
    application.add_handler(conv_welcome_autodel, group=1)
    
    conv_welcome_btn = ConversationHandler(
        entry_points=[CallbackQueryHandler(entry_add_welcome_button, pattern="^add_welcome_button$")],
        states={
            ADD_WELCOME_BUTTON_LABEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_welcome_button_label_handler)],
            ADD_WELCOME_BUTTON_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_welcome_button_url_handler)],
        },
        fallbacks=[],
        per_message=False,
    )
    application.add_handler(conv_welcome_btn, group=1)
    
    # Custom block settings
    conv_custom_block = ConversationHandler(
        entry_points=[CallbackQueryHandler(entry_add_custom_block, pattern="^add_custom_block$")],
        states={
            ADD_CUSTOM_BLOCK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_custom_block_handler)],
        },
        fallbacks=[],
        per_message=False,
    )
    application.add_handler(conv_custom_block, group=1)
    
    # Custom block media settings
    conv_custom_block_media = ConversationHandler(
        entry_points=[CallbackQueryHandler(entry_add_custom_block_media, pattern="^add_custom_block_media$")],
        states={
            ADD_CUSTOM_BLOCK_MEDIA: [MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL | filters.AUDIO | filters.VOICE | filters.VIDEO_NOTE, add_custom_block_media_handler)],
        },
        fallbacks=[],
        per_message=False,
    )
    application.add_handler(conv_custom_block_media, group=1)
    
    # Custom block sticker settings
    conv_custom_block_sticker = ConversationHandler(
        entry_points=[CallbackQueryHandler(entry_add_custom_block_sticker, pattern="^add_custom_block_sticker$")],
        states={
            ADD_CUSTOM_BLOCK_STICKER: [MessageHandler(filters.Sticker.ALL, add_custom_block_sticker_handler)],
        },
        fallbacks=[],
        per_message=False,
    )
    application.add_handler(conv_custom_block_sticker, group=1)
    
    # Antiflood settings
    conv_flood_msgs = ConversationHandler(
        entry_points=[CallbackQueryHandler(entry_set_flood_msgs, pattern="^set_flood_msgs$")],
        states={
            SET_FLOOD_MSGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_flood_msgs_handler)],
        },
        fallbacks=[],
        per_message=False,
    )
    application.add_handler(conv_flood_msgs, group=1)
    
    conv_flood_time = ConversationHandler(
        entry_points=[CallbackQueryHandler(entry_set_flood_time, pattern="^set_flood_time$")],
        states={
            SET_FLOOD_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_flood_time_handler)],
        },
        fallbacks=[],
        per_message=False,
    )
    application.add_handler(conv_flood_time, group=1)
    
    # Recurring message settings
    conv_recurring_text = ConversationHandler(
        entry_points=[CallbackQueryHandler(entry_set_recurring_text, pattern="^set_recurring_text$")],
        states={
            SET_RECURRING_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_recurring_text_handler)],
        },
        fallbacks=[],
        per_message=False,
    )
    application.add_handler(conv_recurring_text, group=1)
    
    conv_recurring_media = ConversationHandler(
        entry_points=[CallbackQueryHandler(entry_set_recurring_media, pattern="^set_recurring_media$")],
        states={
            SET_RECURRING_MEDIA: [MessageHandler(filters.ALL, set_recurring_media_handler)],
        },
        fallbacks=[],
        per_message=False,
    )
    application.add_handler(conv_recurring_media, group=1)
    
    conv_recurring_btn = ConversationHandler(
        entry_points=[CallbackQueryHandler(entry_add_recurring_button, pattern="^add_recurring_button$")],
        states={
            ADD_RECURRING_BUTTON_LABEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_recurring_button_label_handler)],
            ADD_RECURRING_BUTTON_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_recurring_button_url_handler)],
        },
        fallbacks=[],
        per_message=False,
    )
    application.add_handler(conv_recurring_btn, group=1)
    
    # Button handler already registered at group=-1 above
    
    print("Bot is starting...")
    application.run_polling()

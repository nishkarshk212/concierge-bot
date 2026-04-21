import html
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity
from telegram.ext import ContextTypes
from config import group_settings, DEFAULT_SETTINGS, get_default_settings, LOG_GROUP_ID, START_IMAGE, SETTINGS_IMAGE, HELP_IMAGE, IMAGE_POOL
from database import get_chat_settings, save_settings
from font import apply_font
from common import check_permission, check_admin_permissions, BOT_VERSION, EMOJI_GEAR, get_premium_emoji
from translation import translate_text
from ui import get_main_settings_keyboard

def get_random_image():
    """Returns a random image from the image pool."""
    return random.choice(IMAGE_POOL)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    try:
        logging.info(f"Start command received from user: {update.effective_user.id}")
        
        if not update.message:
            logging.error("No message in update for /start command")
            return
        
        # Check if start has parameters (e.g., settings_{group_chat_id})
        if context.args:
            start_param = context.args[0]
            logging.info(f"Start parameter: {start_param}")
            
            # Handle settings_{group_chat_id}
            if start_param.startswith("settings_"):
                try:
                    group_chat_id = int(start_param.replace("settings_", ""))
                    logging.info(f"Opening settings for group: {group_chat_id}")
                    
                    # Load the group settings
                    await get_chat_settings(group_chat_id)
                    
                    # Store the group chat_id in user_data for callback handlers
                    context.user_data['setting_chat_id'] = group_chat_id
                    
                    # Get group info
                    try:
                        group_chat = await context.bot.get_chat(group_chat_id)
                        group_name = group_chat.title or "Unknown Group"
                        
                        # Try to get group mention (username if available)
                        if group_chat.username:
                            group_mention = f"@{group_chat.username}"
                        else:
                            group_mention = group_name
                    except Exception as e:
                        logging.error(f"Error getting group info: {e}")
                        group_mention = "Unknown Group"
                    
                    user_mention = update.effective_user.mention_html() if update.effective_user.username else update.effective_user.first_name
                    
                    gear = get_premium_emoji(EMOJI_GEAR, "🛠")
                    text = (
                        f"{gear} <b>Bot Settings</b> {gear}\n\n"
                        f"<b>Group:</b> {group_mention}\n"
                        f"<b>ID:</b> <code>{group_chat_id}</code>\n"
                        f"<b>Opened by:</b> {user_mention}\n\n"
                        f"Select one of the settings that you want to change:"
                    )
                    reply_markup = await get_main_settings_keyboard()
                    
                    random_image = get_random_image()
                    await update.message.reply_photo(photo=random_image, caption=text, reply_markup=reply_markup, parse_mode='HTML')
                    return
                except ValueError as e:
                    logging.error(f"Invalid group chat_id in start parameter: {e}")
        
        bot = await context.bot.get_me()
        bot_mention = f"[{bot.first_name}](t.me/{bot.username})"
        
        text = (
            f"👋 {apply_font('Hello!')}\n"
            f"{bot_mention} {apply_font('is the most complete Bot to help you manage your groups easily and safely!')}\n\n"
            f"👉 {apply_font('Add me in a Supergroup and promote me as Admin to let me get in action!')}\n\n"
            f"{apply_font('Check my buttons below to get more info about me.')}"
        )
        
        keyboard = [
            [InlineKeyboardButton(f"➕ {apply_font('Add me to a Group')} ➕", url=f"https://t.me/{bot.username}?startgroup=true")],
            [InlineKeyboardButton(f"⚙️ {apply_font('Manage group Settings')} ✍️", callback_data="settings_main")],
            [
                InlineKeyboardButton(f"👥 {apply_font('Group')}", url="https://t.me/bot_support_23"),
                InlineKeyboardButton(f"{apply_font('Channel')} 📢", url="https://t.me/jayden_clan")
            ],
            [
                InlineKeyboardButton(f"👨‍ {apply_font('Support')}", url="https://t.me/Tele_212_bots"),
                InlineKeyboardButton(f"{apply_font('Information')} 💬", callback_data="info")
            ],
            [InlineKeyboardButton(f"🇬🇧 {apply_font('Languages')} 🇮🇹", callback_data="languages")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        logging.info(f"Attempting to send start message to user: {update.effective_user.id}")
        try:
            random_image = get_random_image()
            await update.message.reply_photo(photo=random_image, caption=text, reply_markup=reply_markup, parse_mode='Markdown')
            logging.info(f"Start photo sent successfully to user: {update.effective_user.id}")
        except Exception as e:
            logging.error(f"Failed to send start photo: {e}")
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown', disable_web_page_preview=True)
            logging.info(f"Start text sent successfully to user: {update.effective_user.id}")
    except Exception as e:
        logging.error(f"Error in start command: {e}", exc_info=True)

async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    rules = settings.get("group_rules", "No rules set yet.")
    
    text = f"<b>{apply_font('Group Rules')}</b>\n\n{rules}"
    await update.message.reply_text(text, parse_mode='HTML')

async def me_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context, "me"):
        return

    user = update.effective_user
    text = (
        f"👤 <b>{apply_font('Your Information')}</b>\n\n"
        f"<b>{apply_font('Name:')}</b> {user.first_name}\n"
        f"<b>{apply_font('ID:')}</b> <code>{user.id}</code>\n"
        f"<b>{apply_font('Username:')}</b> @{user.username if user.username else 'None'}\n"
        f"<b>{apply_font('Language:')}</b> {user.language_code}\n"
    )
    await update.message.reply_text(text, parse_mode='HTML')

async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context, "translate"):
        return

    if not update.message.reply_to_message or not update.message.reply_to_message.text:
        await update.message.reply_text(apply_font("Reply to a message to translate it!"))
        return

    target_lang = "en"
    if context.args:
        target_lang = context.args[0]

    text_to_translate = update.message.reply_to_message.text
    translated = translate_text(text_to_translate, target_lang)
    await update.message.reply_text(f"🌍 <b>{apply_font('Translated:')}</b>\n\n{translated}", parse_mode='HTML')

async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context, "link"):
        return

    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text(apply_font("Use this command in a group!"))
        return

    chat_id = chat.id
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    custom_link = settings.get("custom_group_link")

    if custom_link:
        await update.message.reply_text(f"🔗 <b>{apply_font('Group Link:')}</b>\n{custom_link}", parse_mode='HTML')
        return

    try:
        link = await context.bot.export_chat_invite_link(chat.id)
        await update.message.reply_text(f"🔗 <b>{apply_font('Group Link:')}</b>\n{link}", parse_mode='HTML')
    except Exception:
        if chat.username:
            await update.message.reply_text(f"🔗 <b>{apply_font('Group Link:')}</b>\nhttps://t.me/{chat.username}", parse_mode='HTML')
        else:
            await update.message.reply_text(apply_font("I don't have permission to get the group link!"))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a comprehensive help message with inline buttons for each feature."""
    chat_id = update.effective_chat.id if update.effective_chat else update.effective_user.id
    
    text = (
        f"<b>🤖 Bot Help & Features</b>\n\n"
        f"Welcome! Click any button below to learn about a specific feature.\n\n"
        f"<b>Categories:</b>\n"
        f"• <b>Admin Commands</b> - Moderation tools\n"
        f"• <b>Settings</b> - Configure bot behavior\n"
        f"• <b>User Features</b> - Commands for everyone\n"
        f"• <b>Anti-Spam</b> - Protection features\n\n"
        f"<i>Tap a button to see detailed information!</i>"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🛡 Admin Commands", callback_data="help_admin"),
            InlineKeyboardButton("⚙️ Settings", callback_data="help_settings")
        ],
        [
            InlineKeyboardButton("👥 User Commands", callback_data="help_users"),
            InlineKeyboardButton("🚫 Anti-Spam", callback_data="help_antispam")
        ],
        [
            InlineKeyboardButton("🔇 Mute/Ban", callback_data="help_muteban"),
            InlineKeyboardButton("📊 Reports", callback_data="help_reports")
        ],
        [
            InlineKeyboardButton("🎨 Media Blocks", callback_data="help_media"),
            InlineKeyboardButton("🔓 Free System", callback_data="help_free")
        ],
        [
            InlineKeyboardButton("👋 Welcome", callback_data="help_welcome"),
            InlineKeyboardButton("🌐 Translation", callback_data="help_translation")
        ],
        [
            InlineKeyboardButton("⚡ Flood Control", callback_data="help_flood"),
            InlineKeyboardButton("📝 Rules", callback_data="help_rules")
        ],
        [
            InlineKeyboardButton("🔍 Info Command", callback_data="help_info"),
            InlineKeyboardButton("👮 Staff", callback_data="help_staff")
        ],
        [
            InlineKeyboardButton("🔗 Link & Filters", callback_data="help_linkfilters"),
            InlineKeyboardButton("💾 Self Destruct", callback_data="help_selfdestruct")
        ],
        [InlineKeyboardButton("❌ Close", callback_data="close_settings")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        random_image = get_random_image()
        await update.message.reply_photo(photo=random_image, caption=text, reply_markup=reply_markup, parse_mode='HTML')
    except Exception as e:
        logging.error(f"Failed to send help photo: {e}")
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

# Help detail messages for each category
HELP_DETAILS = {
    "admin": (
        "<b>🛡 Admin Commands</b>\n\n"
        "<b>/admin</b> - Promote user to admin\n"
        "<b>/unadmin</b> - Demote user from admin\n"
        "<b>/free</b> - Exempt user from blocks\n"
        "<b>/unfree</b> - Remove exemption\n"
        "<b>/reload</b> - Refresh group data\n\n"
        "<i>These commands require admin rights.</i>"
    ),
    "settings": (
        "<b>⚙️ Settings Panel</b>\n\n"
        "<b>/settings</b> - Open configuration panel\n\n"
        "<b>Available Settings:</b>\n"
        "• <b>Block</b> - Configure content blocking\n"
        "• <b>Welcome</b> - Welcome message setup\n"
        "• <b>Anti-Spam</b> - Spam protection\n"
        "• <b>Anti-Flood</b> - Flood control\n"
        "• <b>Permissions</b> - User permissions\n"
        "• <b>Members Mgmt</b> - Member management\n\n"
        "<i>Only admins can access settings.</i>"
    ),
    "users": (
        "<b>👥 User Commands</b>\n\n"
        "<b>/start</b> - Start the bot\n"
        "<b>/me</b> - View your profile info\n"
        "<b>/translate</b> - Translate messages\n"
        "<b>/rules</b> - View group rules\n\n"
        "<i>These commands are available to everyone.</i>"
    ),
    "antispam": (
        "<b>🚫 Anti-Spam Features</b>\n\n"
        "<b>Automatic Protection:</b>\n"
        "• <b>Link Blocking</b> - Blocks Telegram links\n"
        "• <b>Forward Blocking</b> - Blocks forwarded msgs\n"
        "• <b>Quote Blocking</b> - Blocks quoted messages\n"
        "• <b>Total Links</b> - Limits link count\n\n"
        "<b>Commands:</b>\n"
        "• Configure via /settings > Anti-Spam\n\n"
        "<i>Configure exceptions for admins/roles.</i>"
    ),
    "muteban": (
        "<b>🔇 Mute & Ban Commands</b>\n\n"
        "<b>/mute</b> - Mute user (reply or ID)\n"
        "• Shows Unmute & Permissions buttons\n\n"
        "<b>/unmute</b> - Unmute user\n\n"
        "<b>/ban</b> - Ban user from group\n"
        "<b>/cban</b> - Channel ban (forward msg)\n"
        "<b>/unban</b> - Unban user\n\n"
        "<i>All commands require admin rights.</i>"
    ),
    "reports": (
        "<b>📊 Report System</b>\n\n"
        "<b>@admin</b> - Report user to admins\n"
        "<b>/report</b> - Same as @admin\n\n"
        "<b>How it works:</b>\n"
        "• Sends report to qualified admins\n"
        "• Admins must have:\n"
        "  - Change Info permission\n"
        "  - Restrict Members permission\n"
        "• Shows user info and action buttons\n\n"
        "<i>Configure in /settings > Reports</i>"
    ),
    "media": (
        "<b>🎨 Media Block Settings</b>\n\n"
        "<b>Blockable Content:</b>\n"
        "• <b>Text Messages</b> - Plain text\n"
        "• <b>Photos</b> - Images\n"
        "• <b>Videos</b> - Video files\n"
        "• <b>Stickers/GIF</b> - Stickers & animations\n"
        "• <b>Audio</b> - Music & audio files\n"
        "• <b>Voice</b> - Voice messages\n"
        "• <b>Files</b> - Documents\n"
        "• <b>Round Video</b> - Video notes\n"
        "• <b>Polls</b> - Polls\n\n"
        "<i>Configure per-user via /free command</i>"
    ),
    "free": (
        "<b>🔓 Free System</b>\n\n"
        "<b>/free [user]</b> - Exempt user from blocks\n"
        "• Opens block exemption panel\n"
        "• Toggle which blocks to exempt\n"
        "• ✅ = Exempt (allowed)\n"
        "• ❌ = Blocked (normal)\n\n"
        "<b>/unfree [user]</b> - Remove all exemptions\n\n"
        "<b>Exemptable Blocks:</b>\n"
        "Stickers, Media, Docs, Forward, Commands,\n"
        "Premium Stickers, Channel Posts, Contact,\n"
        "Location, Voice, Video Notes, Polls, Links\n\n"
        "<i>Great for trusted members!</i>"
    ),
    "welcome": (
        "<b>👋 Welcome System</b>\n\n"
        "<b>Features:</b>\n"
        "• <b>Custom Message</b> - Set welcome text\n"
        "• <b>Media</b> - Photo/Video/GIF welcome\n"
        "• <b>Buttons</b> - Add URL buttons\n"
        "• <b>Auto-Delete</b> - Auto-remove after time\n\n"
        "<b>Setup:</b>\n"
        "1. /settings > Welcome\n"
        "2. Configure message & media\n"
        "3. Add custom buttons (optional)\n"
        "4. Set auto-delete timer\n\n"
        "<i>Variables: {first}, {last}, {username}</i>"
    ),
    "translation": (
        "<b>🌐 Translation Feature</b>\n\n"
        "<b>/translate [lang]</b> - Translate message\n"
        "• Reply to any message\n"
        "• Specify language code (en, hi, etc.)\n\n"
        "<b>Example:</b>\n"
        "• /translate en - Translate to English\n"
        "• /translate hi - Translate to Hindi\n\n"
        "<i>Supports 100+ languages via Google Translate</i>"
    ),
    "flood": (
        "<b>⚡ Flood Control</b>\n\n"
        "<b>Prevents spam flooding:</b>\n"
        "• <b>Message Limit</b> - Max msgs in time window\n"
        "• <b>Time Window</b> - Seconds to track\n\n"
        "<b>Setup:</b>\n"
        "1. /settings > Anti-Flood\n"
        "2. Set message count (e.g., 5)\n"
        "3. Set time window (e.g., 10 sec)\n"
        "4. Enable protection\n\n"
        "<i>Violators get muted automatically</i>"
    ),
    "rules": (
        "<b>📝 Rules System</b>\n\n"
        "<b>/rules</b> - Display group rules\n\n"
        "<b>Setup:</b>\n"
        "1. /settings > Rules\n"
        "2. Set rules text\n"
        "3. Configure who can use /rules\n\n"
        "<b>Options:</b>\n"
        "• Show to everyone\n"
        "• Show to members only\n"
        "• Show to admins only\n\n"
        "<i>Keep rules clear and concise!</i>"
    ),
    "info": (
        "<b>🔍 Info Command</b>\n\n"
        "<b>/info [user]</b> - Get user information\n"
        "• Reply to user or provide ID\n\n"
        "<b>Shows:</b>\n"
        "• User name & ID\n"
        "• Username\n"
        "• Warn count (X/3)\n"
        "• Role status (Free, etc.)\n"
        "• Permission status\n\n"
        "<b>Action Buttons:</b>\n"
        "• ❗ Warns - View warn details\n"
        "• ➰ Roles - View/set roles\n"
        "• 🔇/🔊 Mute/Unmute - Toggle mute\n"
        "• 🚫/✅ Ban/Unban - Toggle ban\n"
        "• 🕹 Permissions - Block exemptions\n\n"
        "<i>Buttons update live based on status</i>"
    ),
    "staff": (
        "<b>👮 Staff Command</b>\n\n"
        "<b>/staff</b> - List all group admins\n"
        "• Shows admins with permissions\n"
        "• Includes creator\n\n"
        "<b>Displays:</b>\n"
        "• Admin name\n"
        "• Admin ID\n"
        "• Permission status\n\n"
        "<i>Useful to see who has admin rights</i>"
    ),
    "linkfilters": (
        "<b>🔗 Link & Filters</b>\n\n"
        "<b>/link</b> - Get group invite link\n\n"
        "<b>Filters:</b>\n"
        "<b>/filter [trigger]</b> - Add auto-response\n"
        "• Bot replies when trigger is detected\n\n"
        "<b>/filters</b> - List all active filters\n\n"
        "<b>/stop [trigger]</b> - Remove filter\n"
        "<b>/stopall</b> - Remove all filters\n\n"
        "<i>Great for FAQs and auto-responses!</i>"
    ),
    "selfdestruct": (
        "<b>💾 Self Destruct Messages</b>\n\n"
        "<b>Features:</b>\n"
        "• Auto-delete messages after time\n"
        "• Configure timer per group\n\n"
        "<b>Setup:</b>\n"
        "1. /settings > Self Destruct\n"
        "2. Set timer (seconds)\n"
        "3. Enable for specific content\n\n"
        "<i>Useful for temporary information</i>"
    )
}

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.type == "private":
        chat_id = update.effective_user.id
        await get_chat_settings(chat_id)
        
        gear = get_premium_emoji(EMOJI_GEAR, "🛠")
        text = f"{gear} Bot Settings {gear}\n\nSelect a category to configure:"
        reply_markup = await get_main_settings_keyboard()
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return

    # Check if user has required admin permissions (can_change_info AND can_restrict_members)
    # Bypass anonymous admin check for settings so they can actually enable it
    has_perm, error_msg = await check_admin_permissions(
        update, context, 
        required_perms=['can_change_info', 'can_restrict_members'],
        bypass_anon_check=True
    )
    if not has_perm:
        await update.message.reply_text(error_msg)
        return

    bot = await context.bot.get_me()
    group_chat_id = update.effective_chat.id
    
    # Store the group chat_id in user_data for callback handlers
    context.user_data['setting_chat_id'] = group_chat_id
    logging.info(f"Stored setting_chat_id: {group_chat_id} for user {update.effective_user.id}")
    
    # Show two buttons: Open Here and Open in Private
    text = "How would you like to open the settings?"
    keyboard = [
        [
            InlineKeyboardButton("Open Here 📍", callback_data="open_settings_here"),
            InlineKeyboardButton("Open in Private 🔐", callback_data="open_settings_private")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
    logging.info(f"Settings choice presented in group {group_chat_id}")

async def on_my_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detects when the bot is added to or removed from a group."""
    if not update.my_chat_member:
        return
    
    chat = update.effective_chat
    user_who_acted = update.my_chat_member.from_user
    bot = await context.bot.get_me()
    
    old_status = update.my_chat_member.old_chat_member.status
    new_status = update.my_chat_member.new_chat_member.status

    if new_status in ["member", "administrator"] and old_status in ["left", "kicked"]:
        if chat.type in ["group", "supergroup"]:
            # Check permissions of the person who added it
            user_id = user_who_acted.id
            try:
                member = await chat.get_member(user_id)
                is_owner = member.status == "creator"
                has_ban_perm = False
                has_change_info_perm = False
                if member.status == "administrator":
                    has_ban_perm = getattr(member, 'can_restrict_members', False)
                    has_change_info_perm = getattr(member, 'can_change_info', False)
                
                if not (is_owner or (has_ban_perm and has_change_info_perm)):
                    await chat.leave()
                    return # Exit after leaving
            except Exception:
                pass

            # Log bot addition using new notification function
            from welcome_feature import notify_bot_added_to_group
            try:
                await notify_bot_added_to_group(
                    update, 
                    context, 
                    chat_id=chat.id, 
                    chat_title=chat.title, 
                    added_by_user=user_who_acted
                )
            except Exception as e:
                logging.error(f"Error logging bot add: {e}")

    elif new_status in ["left", "kicked"] and old_status in ["member", "administrator"]:
        # Log bot removal
        try:
            log_text = (
                f"📝 {bot.mention_html()} ʟᴇꜰᴛ ᴀ ɢʀᴏᴜᴘ\n\n"
                f"❅─────✧❅✦❅✧─────❅\n\n"
                f"📌 ᴄʜᴀᴛ ɴᴀᴍᴇ: {chat.title}\n"
                f"🍂 ᴄʜᴀᴛ ɪᴅ: <code>{chat.id}</code>\n"
                f"🔐 ᴄʜᴀᴛ ᴜsᴇʀɴᴀᴍᴇ: @{chat.username if chat.username else 'None'}\n"
                f"🤔 ʀᴇᴍᴏᴠᴇᴅ ʙʏ: {user_who_acted.mention_html()}"
            )
            await context.bot.send_message(LOG_GROUP_ID, log_text, parse_mode='HTML')
        except Exception as e:
            logging.error(f"Error logging bot leave: {e}")

async def extract_emoji_pack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg.entities:
        return
    custom_emoji_ids = [entity.custom_emoji_id for entity in msg.entities if entity.type == MessageEntity.CUSTOM_EMOJI]
    if not custom_emoji_ids:
        return
    emoji_id = custom_emoji_ids[0]
    try:
        stickers = await context.bot.get_custom_emoji_stickers([emoji_id])
        if not stickers:
            await msg.reply_text(apply_font("Could not find sticker info for this emoji."))
            return
        sticker = stickers[0]
        set_name = sticker.set_name
        if not set_name:
            await msg.reply_text(apply_font("This emoji doesn't seem to belong to a pack."))
            return
        sticker_set = await context.bot.get_sticker_set(set_name)
        emoji_list = []
        for s in sticker_set.stickers:
            if s.custom_emoji_id:
                emoji_list.append(f"<tg-emoji emoji-id='{s.custom_emoji_id}'>{s.emoji or '?'}</tg-emoji>")
        chunk_size = 50
        for i in range(0, len(emoji_list), chunk_size):
            chunk = emoji_list[i:i + chunk_size]
            title = apply_font(f"Pack: {sticker_set.title}") if i == 0 else ""
            response = f"{title}\n\n" + " ".join(chunk)
            await msg.reply_text(response, parse_mode='HTML')
    except Exception as e:
        logging.error(f"Error extracting emoji pack: {e}")
        await msg.reply_text(apply_font("An error occurred while extracting the emoji pack."))

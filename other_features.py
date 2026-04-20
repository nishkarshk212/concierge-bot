import html
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity
from telegram.ext import ContextTypes
from config import group_settings, DEFAULT_SETTINGS, get_default_settings
from database import get_chat_settings, save_settings
from font import apply_font
from common import check_permission, BOT_VERSION, EMOJI_GEAR, get_premium_emoji
from translation import translate_text
from ui import get_main_settings_keyboard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    bot = await context.bot.get_me()
    bot_mention = f"[{bot.first_name}](t.me/{bot.username})"
    
    text = (
        f"👋 {apply_font('Hello!')}\n"
        f"{bot_mention} {apply_font('is the most complete Bot to help you manage your groups easily and safely!')}\n\n"
        f"👉 {apply_font('Add me in a Supergroup and promote me as Admin to let me get in action!')}\n\n"
        f"<i>{apply_font('Check my buttons below to get more info about me.')}</i>"
    )
    
    keyboard = [
        [InlineKeyboardButton(f"➕ {apply_font('Add me to a Group')} ➕", url=f"https://t.me/{bot.username}?startgroup=true")],
        [InlineKeyboardButton(f"⚙️ {apply_font('Manage group Settings')} ✍️", callback_data="settings_main")],
        [
            InlineKeyboardButton(f"👥 {apply_font('Group')}", url="https://t.me/bot_support_23"),
            InlineKeyboardButton(f"{apply_font('Channel')} 📢", url="https://t.me/jayden_clan")
        ],
        [
            InlineKeyboardButton(f"👨‍💻 {apply_font('Support')}", url="https://t.me/Tele_212_bots"),
            InlineKeyboardButton(f"{apply_font('Information')} 💬", callback_data="info")
        ],
        [InlineKeyboardButton(f"🇬🇧 {apply_font('Languages')} 🇮🇹", callback_data="languages")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown', disable_web_page_preview=True)

async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context, "rules"):
        return

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
    """Sends a help message."""
    text = (
        f"❓ {apply_font('Help Menu')} ❓\n\n"
        f"1. {apply_font('/start - Start the bot')}\n"
        f"2. {apply_font('/settings - Open settings (Admins only)')}\n"
        f"3. {apply_font('/help - Show this message')}\n\n"
        f"{apply_font('The bot automatically blocks content based on the settings configured in each group.')}\n"
        f"{apply_font('In private chat, send a premium emoji to extract its pack!')}"
    )
    await update.message.reply_text(text, parse_mode='HTML')

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.type == "private":
        chat_id = update.effective_user.id
        await get_chat_settings(chat_id)
        
        gear = get_premium_emoji(EMOJI_GEAR, "🛠")
        text = f"{gear} " + apply_font("Bot Settings") + f" {gear}\n\n" + apply_font("Select a category to configure:")
        reply_markup = await get_main_settings_keyboard()
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return

    member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    if member.status not in ["administrator", "creator"]:
        await update.message.reply_text(apply_font("Only admins can change settings!"))
        return

    bot = await context.bot.get_me()
    text = apply_font("How would you like to open the settings?")
    keyboard = [
        [
            InlineKeyboardButton(apply_font("Open Here 📍"), callback_data="open_settings_here"),
            InlineKeyboardButton(apply_font("Open in Private 🔐"), url=f"https://t.me/{bot.username}?start=settings")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def on_my_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detects when the bot is added to a group and checks permissions of the person who added it."""
    if not update.my_chat_member:
        return
    result = update.my_chat_member.difference()
    if not result:
        return
    old_status, new_status = result.status
    if new_status in ["member", "administrator"] and old_status in ["left", "kicked"]:
        chat = update.effective_chat
        if chat.type in ["group", "supergroup"]:
            user_who_added = update.my_chat_member.from_user
            user_id = user_who_added.id
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
            except Exception:
                pass

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

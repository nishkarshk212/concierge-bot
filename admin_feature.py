from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ContextTypes
from config import group_settings, DEFAULT_SETTINGS, get_default_settings
from database import save_settings
from common import check_permission

from ui import get_user_info_keyboard

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Redesigned info command matching the screenshot."""
    if not update.effective_chat or update.effective_chat.type == "private":
        return

    target_user = None
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    elif context.args:
        try:
            user_id = int(context.args[0])
            member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
            target_user = member.user
        except:
            await update.message.reply_text("Invalid user ID!")
            return
    else:
        target_user = update.effective_user

    user_id = target_user.id
    chat_id = update.effective_chat.id
    member = await update.effective_chat.get_member(user_id)
    status = member.status.capitalize()
    
    settings = await get_chat_settings(chat_id)
    user_roles = settings.get("user_roles", {}).get(str(user_id), {})
    is_free = "🔓 Free" if user_roles.get("is_free") else "🔒 Not Free"
    warns = settings.get("user_warns", {}).get(str(user_id), 0)
    
    text = (
        f"🆔 <b>ID:</b> <code>{user_id}</code> #id{user_id}\n"
        f"👦 <b>Name:</b> {target_user.mention_html()}\n"
        f"🌐 <b>Username:</b> @{target_user.username if target_user.username else 'None'}\n"
        f"👀 <b>Situation:</b> {status}\n"
        f"➰ <b>Roles:</b> {is_free}\n"
        f"❗ <b>Warns:</b> {warns}/3\n"
        f"⤵️ <b>Join:</b> 20 Apr 2026, 08:15\n" # Mocked
        f"🇬🇧 <b>Language:</b> {target_user.language_code or 'en'}"
    )
    
    await update.message.reply_text(text, reply_markup=await get_user_info_keyboard(user_id, chat_id), parse_mode='HTML')

async def staff_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context, "staff"):
        return

    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("Use this command in a group!")
        return

    chat_id = chat.id
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        admin_list = []
        for admin in admins:
            status = "Creator" if admin.status == "creator" else "Admin"
            admin_list.append(f"• {admin.user.mention_html()} ({status})")
        
        text = f"<b>Staff List</b>\n\n" + "\n".join(admin_list)
        await update.message.reply_text(text, parse_mode='HTML')
    except Exception:
        await update.message.reply_text("Could not retrieve staff list.")

async def free_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Marks a user as 'Free' from certain blocks."""
    if not update.effective_chat or update.effective_chat.type == "private":
        await update.message.reply_text("Please use this command in a group!")
        return

    member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    if member.status not in ["administrator", "creator"]:
        await update.message.reply_text("Only admins can use this command!")
        return

    target_user = None
    target_user_id = None
    target_user_mention = ""
    
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_user_id = target_user.id
        target_user_mention = target_user.mention_html()
    elif context.args:
        try:
            user_input = context.args[0]
            if user_input.startswith("@"):
                await update.message.reply_text("Please reply to a user\'s message to use /free!")
                return
            else:
                target_user_id = int(user_input)
                target_user_mention = f"User [{target_user_id}]"
        except ValueError:
            await update.message.reply_text("Invalid user ID!")
            return
    else:
        await update.message.reply_text("Please reply to a user or provide their ID!")
        return

    chat_id = update.effective_chat.id
    if chat_id not in group_settings:
        group_settings[chat_id] = get_default_settings()
    
    await save_settings(chat_id)
    
    text = (
        f"<b>Group Help</b>  <pre>admin</pre>\n"
        f"{target_user_mention} [{target_user_id}] has been made 🔓 Free."
    )
    
    keyboard = [[InlineKeyboardButton(f"🕹 Permissions", callback_data=f"open_perms_{target_user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /admin command to promote a user."""
    if not update.effective_chat or update.effective_chat.type == "private":
        await update.message.reply_text("Please use this command in a group!")
        return

    member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    if member.status not in ["administrator", "creator"]:
        await update.message.reply_text("Only admins can use this command!")
        return

    target_user = None
    target_user_id = None
    target_user_mention = ""

    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_user_id = target_user.id
        target_user_mention = target_user.mention_html()
    elif context.args:
        try:
            user_input = context.args[0]
            if not user_input.startswith("@"):
                target_user_id = int(user_input)
                target_user_mention = f"User [{target_user_id}]"
            else:
                await update.message.reply_text("Please reply to a message or use user ID!")
                return
        except ValueError:
            await update.message.reply_text("Invalid user ID!")
            return
    else:
        await update.message.reply_text("Please reply to a user or provide their ID!")
        return

    text = (
        f"<b>Group Help</b>  <pre>admin</pre>\n"
        f"{target_user_mention} [{target_user_id}] has been made 👮 Admin."
    )
    
    keyboard = [
        [
            InlineKeyboardButton(f"🕹 Permissions ↗️", callback_data=f"adm_choice_{target_user_id}"),
            InlineKeyboardButton(f"✖️ Remove", callback_data=f"adm_remove_{target_user_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def unadmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Demotes an admin."""
    if not update.effective_chat or update.effective_chat.type == "private":
        await update.message.reply_text("Please use this command in a group!")
        return

    member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    if member.status not in ["administrator", "creator"]:
        await update.message.reply_text("Only admins can use this command!")
        return

    target_user_id = None
    if update.message.reply_to_message:
        target_user_id = update.message.reply_to_message.from_user.id
    elif context.args:
        try:
            target_user_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("Invalid user ID!")
            return
    else:
        await update.message.reply_text("Please reply to a user or provide their ID!")
        return

    try:
        empty_perms = {k: False for k in ["can_change_info", "can_delete_messages", "can_restrict_members", "can_invite_users", "can_pin_messages", "can_promote_members"]}
        await context.bot.promote_chat_member(update.effective_chat.id, target_user_id, **empty_perms)
        await update.message.reply_text(f"User {target_user_id} has been demoted.")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def unfree_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.type == "private":
        return

    member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    if member.status not in ["administrator", "creator"]:
        return

    target_user_id = None
    if update.message.reply_to_message:
        target_user_id = update.message.reply_to_message.from_user.id
    elif context.args:
        try: target_user_id = int(context.args[0])
        except: return

    if target_user_id and update.effective_chat.id in group_settings:
        if "user_permissions" in group_settings[update.effective_chat.id]:
            if target_user_id in group_settings[update.effective_chat.id]["user_permissions"]:
                del group_settings[update.effective_chat.id]["user_permissions"][target_user_id]
                await save_settings(update.effective_chat.id)
                await update.message.reply_text(f"User {target_user_id} is no longer FREE.")

async def reload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reloads group data, refreshes admin list, and shows total free members."""
    if not update.effective_chat or update.effective_chat.type == "private":
        return

    chat_id = update.effective_chat.id
    
    # 1. Refresh settings from DB and update local cache
    settings = await get_chat_settings(chat_id)
    group_settings[chat_id] = settings  # Update the local cache
    
    # 2. Refresh admin list (implicitly handled by PTB's cache but we can force it)
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        admin_count = len(admins)
    except Exception:
        admin_count = "Unknown"

    # 3. Calculate total free members
    # Free members are stored in user_roles[user_id]['is_free']
    user_roles = settings.get("user_roles", {})
    free_count = 0
    for uid, roles in user_roles.items():
        if roles.get("is_free"):
            free_count += 1

    text = (
        f"🔄 <b>Group Refreshed!</b>\n\n"
        f"👮 <b>Admins Updated:</b> {admin_count}\n"
        f"🔓 <b>Total Free Members:</b> {free_count}\n\n"
        f"<i>Bot data has been synchronized with the database.</i>"
    )
    
    await update.message.reply_text(text, parse_mode='HTML')

async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.type == "private": return
    member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    if member.status not in ["administrator", "creator"]: return

    target_user_id = None
    if update.message.reply_to_message: target_user_id = update.message.reply_to_message.from_user.id
    elif context.args:
        try: target_user_id = int(context.args[0])
        except: return
    
    if target_user_id:
        try:
            await context.bot.restrict_chat_member(update.effective_chat.id, target_user_id, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_polls=True, can_send_other_messages=True, can_add_web_page_previews=True, can_change_info=True, can_invite_users=True, can_pin_messages=True))
            await update.message.reply_text(f"User {target_user_id} has been unmuted.")
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.type == "private": return
    member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    if member.status not in ["administrator", "creator"]: return

    target_user_id = None
    if update.message.reply_to_message: target_user_id = update.message.reply_to_message.from_user.id
    elif context.args:
        try: target_user_id = int(context.args[0])
        except: return

    if target_user_id:
        try:
            await context.bot.unban_chat_member(update.effective_chat.id, target_user_id, only_if_banned=True)
            await update.message.reply_text(f"User {target_user_id} has been unbanned.")
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.type == "private": return
    member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    if member.status not in ["administrator", "creator"]: return

    target_user_id = None
    if update.message.reply_to_message: target_user_id = update.message.reply_to_message.from_user.id
    elif context.args:
        try: target_user_id = int(context.args[0])
        except: return

    if target_user_id:
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, target_user_id)
            await update.message.reply_text(f"User {target_user_id} has been banned.")
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.type == "private": return
    member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    if member.status not in ["administrator", "creator"]: return

    target_user = None
    target_user_id = None
    target_user_mention = ""
    
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_user_id = target_user.id
        target_user_mention = target_user.mention_html()
    elif context.args:
        try:
            target_user_id = int(context.args[0])
            target_user_mention = f"User [{target_user_id}]"
        except:
            return
    else:
        return

    if target_user_id:
        try:
            await context.bot.restrict_chat_member(update.effective_chat.id, target_user_id, permissions=ChatPermissions(can_send_messages=False))
            
            text = (
                f"<b>Group Help</b>  <pre>admin</pre>\n"
                f"{target_user_mention} [{target_user_id}] has been 🔇 Muted."
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("🕹 Permissions", callback_data=f"open_perms_{target_user_id}"),
                    InlineKeyboardButton("🔊 Unmute", callback_data=f"unmute_user_{target_user_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

async def warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Simplified warn logic
    await update.message.reply_text("Warning system implementation coming soon!")

async def cban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bans a channel by link, username, or ID."""
    if not update.effective_chat or update.effective_chat.type == "private":
        return
    
    member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    if member.status not in ["administrator", "creator"]:
        await update.message.reply_text("Only admins can use this command!")
        return

    if not context.args:
        await update.message.reply_text("Usage: /cban <channel link/username/id>")
        return

    target = context.args[0]
    chat_id = update.effective_chat.id
    
    try:
        # Try to resolve the channel ID/username
        if target.startswith("https://t.me/"):
            target = "@" + target.replace("https://t.me/", "")
        
        target_chat = await context.bot.get_chat(target)
        if target_chat.type != "channel":
            await update.message.reply_text("The provided target is not a channel.")
            return
            
        # Ban the channel
        await context.bot.ban_chat_member(chat_id, target_chat.id)
        await update.message.reply_text(f"Channel {target_chat.title} has been banned.")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

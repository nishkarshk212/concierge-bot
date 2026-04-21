from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ContextTypes
from config import group_settings, DEFAULT_SETTINGS, get_default_settings
from database import save_settings, get_chat_settings
from common import check_permission, check_admin_permissions
import logging

from ui import get_user_info_keyboard

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Redesigned info command matching the screenshot."""
    if not update.effective_chat or update.effective_chat.type == "private":
        return
    
    # Check command permissions
    if not await check_permission(update, context, "info"):
        return

    target_user = None
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    elif context.args:
        arg = context.args[0]
        # Try to parse as user ID first
        try:
            user_id = int(arg)
            member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
            target_user = member.user
        except ValueError:
            # Not an ID, try username resolution
            user_id, user_name, error = await resolve_user(context, update.effective_chat.id, arg)
            if error:
                await update.message.reply_text(error)
                return
            if user_id:
                member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
                target_user = member.user
    else:
        target_user = update.effective_user

    user_id = target_user.id
    chat_id = update.effective_chat.id
    member = await update.effective_chat.get_member(user_id)
    status = member.status
    
    # Determine role display
    if status == "creator":
        role_display = "👑 Creator"
    elif status == "administrator":
        # Check if admin has co-founder permissions (can_change_info and can_restrict_members)
        is_co_founder = (
            member.can_change_info and 
            member.can_restrict_members
        )
        role_display = "🌟 Co Founder" if is_co_founder else "👤 Admin"
    elif status == "member":
        role_display = "👥 Member"
    else:
        role_display = status.capitalize()
    
    settings = await get_chat_settings(chat_id)
    user_roles = settings.get("user_roles", {}).get(str(user_id), {})
    is_free = "🔓 Free" if user_roles.get("is_free") else "🔒 Not Free"
    warns = settings.get("user_warns", {}).get(str(user_id), 0)
    
    text = (
        f"🆔 <b>ID:</b> <code>{user_id}</code> #id{user_id}\n"
        f"👦 <b>Name:</b> {target_user.mention_html()}\n"
        f"🌐 <b>Username:</b> @{target_user.username if target_user.username else 'None'}\n"
        f"👀 <b>Role:</b> {role_display}\n"
        f"➰ <b>Roles:</b> {is_free}\n"
        f"❗ <b>Warns:</b> {warns}/3\n"
        f"⤵️ <b>Join:</b> 20 Apr 2026, 08:15\n" # Mocked
        f"🇬🇧 <b>Language:</b> {target_user.language_code or 'en'}"
    )
    
    await update.message.reply_text(text, reply_markup=await get_user_info_keyboard(user_id, chat_id, context), parse_mode='HTML')

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
    # Check if user has required admin permissions (can_change_info AND can_restrict_members)
    has_perm, error_msg = await check_admin_permissions(
        update, context, 
        required_perms=['can_change_info', 'can_restrict_members']
    )
    if not has_perm:
        await update.message.reply_text(error_msg)
        return

    target_user = None
    target_user_id = None
    target_user_mention = ""
    
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_user_id = target_user.id
        target_user_mention = target_user.mention_html()
    elif context.args:
        arg = context.args[0]
        target_user_id, target_user_name, error = await resolve_user(context, update.effective_chat.id, arg)
        if error:
            await update.message.reply_text(error)
            return
        if target_user_id:
            target_user_mention = f"<a href='tg://user?id={target_user_id}'>{target_user_name or 'User'}</a>"
    else:
        await update.message.reply_text("Please reply to a user or provide their ID/username!")
        return

    chat_id = update.effective_chat.id
    if chat_id not in group_settings:
        group_settings[chat_id] = get_default_settings()
    
    # Check if user is already free
    if "user_roles" not in group_settings[chat_id]:
        group_settings[chat_id]["user_roles"] = {}
    
    if str(target_user_id) not in group_settings[chat_id]["user_roles"]:
        group_settings[chat_id]["user_roles"][str(target_user_id)] = {}
        
    if group_settings[chat_id]["user_roles"][str(target_user_id)].get("is_free"):
        # User is already free, show blocking settings panel
        text = (
            f"⚠️ <b>{target_user_mention}</b> [{target_user_id}] is already FREE!\n\n"
            f"💡 You can still manage their blocking permissions below:"
        )
        
        # Import the blocking settings keyboard
        from ui import get_blocking_settings_keyboard
        reply_markup = await get_blocking_settings_keyboard(chat_id)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return
    
    # Set as free
    group_settings[chat_id]["user_roles"][str(target_user_id)]["is_free"] = True
    await save_settings(chat_id)
    
    text = (
        f"<b>Group Help</b>  <pre>admin</pre>\n"
        f"{target_user_mention} [{target_user_id}] has been made 🔓 Free.\n\n"
        f"💡 Manage blocking permissions below:"
    )
    
    # Import the blocking settings keyboard
    from ui import get_blocking_settings_keyboard
    reply_markup = await get_blocking_settings_keyboard(chat_id)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /admin or /promote command to promote a user to admin."""
    # Check if user has required admin permissions (can_change_info AND can_restrict_members)
    has_perm, error_msg = await check_admin_permissions(
        update, context, 
        required_perms=['can_change_info', 'can_restrict_members']
    )
    if not has_perm:
        await update.message.reply_text(error_msg)
        return

    target_user = None
    target_user_id = None
    target_user_mention = ""

    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_user_id = target_user.id
        target_user_mention = target_user.mention_html()
    elif context.args:
        arg = context.args[0]
        target_user_id, target_user_name, error = await resolve_user(context, update.effective_chat.id, arg)
        if error:
            await update.message.reply_text(error)
            return
        if target_user_id:
            target_user_mention = f"<a href='tg://user?id={target_user_id}'>{target_user_name or 'User'}</a>"
    else:
        await update.message.reply_text("Please reply to a user or provide their ID/username!")
        return

    # Check if user is already an admin
    try:
        target_member = await context.bot.get_chat_member(update.effective_chat.id, target_user_id)
        if target_member.status in ["administrator", "creator"]:
            await update.message.reply_text(
                f"⚠️ <b>{target_user_mention}</b> [{target_user_id}] is already an admin!"
            )
            return
    except Exception:
        pass  # If we can't get member info, proceed with promotion

    # Promote user to admin with minimal permissions first
    try:
        # Get bot's own permissions to ensure we don't try to grant permissions the bot doesn't have
        bot_member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
        bot_perms = bot_member if bot_member.status == "administrator" else None
        
        # Only grant permissions that the bot itself has
        await context.bot.promote_chat_member(
            chat_id=update.effective_chat.id,
            user_id=target_user_id,
            can_change_info=bot_perms.can_change_info if bot_perms else False,
            can_delete_messages=bot_perms.can_delete_messages if bot_perms else False,
            can_restrict_members=bot_perms.can_restrict_members if bot_perms else False,
            can_invite_users=bot_perms.can_invite_users if bot_perms else False,
            can_pin_messages=bot_perms.can_pin_messages if bot_perms else False,
            can_promote_members=False,  # Never grant this - only owner should have it
            is_anonymous=False
        )
    except Exception as e:
        error_msg = str(e)
        logging.error(f"[ADMIN] Failed to promote user: {error_msg}")
        await update.message.reply_text(f"❌ Failed to promote user: {error_msg}\n\n<i>Make sure the bot has 'Add New Admins' permission.</i>", parse_mode='HTML')
        return

    text = (
        f"<b>Group Help</b>  <pre>admin</pre>\n"
        f"{target_user_mention} [{target_user_id}] has been made 👮 Admin.\n\n"
        f"<i>Click '🕹 Permissions' to configure admin permissions, or '✖️ Remove' to demote.</i>"
    )
    
    keyboard = [
        [
            InlineKeyboardButton(f"🕹 Permissions ↗️", callback_data=f"adm_choice_{target_user_id}"),
            InlineKeyboardButton(f"✖️ Demote", callback_data=f"adm_remove_{target_user_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def unadmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /unadmin or /demote command to demote an admin to normal member."""
    # Check if user has required admin permissions
    # To demote admins, user needs can_promote_members permission
    has_perm, error_msg = await check_admin_permissions(
        update, context, 
        required_perms=['can_promote_members']
    )
    if not has_perm:
        await update.message.reply_text(error_msg)
        return

    target_user_id = None
    target_user_name = None
    
    if update.message.reply_to_message:
        target_user_id = update.message.reply_to_message.from_user.id
        target_user_name = update.message.reply_to_message.from_user.first_name
    elif context.args:
        arg = context.args[0]
        target_user_id, target_user_name, error = await resolve_user(context, update.effective_chat.id, arg)
        if error:
            await update.message.reply_text(error)
            return
    else:
        await update.message.reply_text("Please reply to a user or provide their ID/username!")
        return

    try:
        # Check if the target user is actually an admin
        target_member = await context.bot.get_chat_member(update.effective_chat.id, target_user_id)
        if target_member.status not in ["administrator", "creator"]:
            await update.message.reply_text(
                f"⚠️ User {target_user_id} is not an admin!"
            )
            return
        
        # Creator cannot be demoted
        if target_member.status == "creator":
            await update.message.reply_text(
                "⚠️ Cannot demote the group creator!"
            )
            return
        
        # Demote admin by removing all admin permissions (makes them a normal member)
        empty_perms = {k: False for k in ["can_change_info", "can_delete_messages", "can_restrict_members", "can_invite_users", "can_pin_messages", "can_promote_members"]}
        await context.bot.promote_chat_member(update.effective_chat.id, target_user_id, **empty_perms)
        
        # Get user mention for better message
        target_user_mention = f"User {target_user_id}"
        try:
            target_user = await context.bot.get_chat(target_user_id)
            if target_user.first_name:
                target_user_mention = target_user.first_name
        except:
            pass
        
        await update.message.reply_text(
            f"✅ <b>{target_user_mention}</b> [{target_user_id}] has been demoted to a normal member.",
            parse_mode='HTML'
        )
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Unadmin error for user {target_user_id}: {error_msg}")
        
        # Check specific error types
        if "Chat_admin_required" in error_msg or "not enough rights" in error_msg.lower():
            # This error means the BOT doesn't have permission to promote/demote
            logging.error(f"Bot missing can_promote_members permission in chat {update.effective_chat.id}")
            await update.message.reply_text(
                "⚠️ <b>Error: Bot Missing Permission</b>\n\n"
                "I need the <b>'Add new admins'</b> permission to demote admins.\n\n"
                "<b>How to fix:</b>\n"
                "1. Go to Group Settings → Administrators\n"
                "2. Find my profile and tap on it\n"
                "3. Enable <b>'Add new admins'</b> permission\n"
                "4. Save and try the command again"
            )
        elif "user is an administrator" in error_msg.lower():
            await update.message.reply_text(
                f"⚠️ User {target_user_id} is already an admin with full rights!"
            )
        else:
            await update.message.reply_text(f"❌ Error: {error_msg}")

async def unfree_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.type == "private":
        return

    # Check admin permissions
    has_perm, error_msg = await check_admin_permissions(
        update, context, 
        required_perms=['can_change_info', 'can_restrict_members']
    )
    if not has_perm:
        await update.message.reply_text(error_msg)
        return

    target_user_id = None
    target_user_name = None
    
    if update.message.reply_to_message:
        target_user_id = update.message.reply_to_message.from_user.id
        target_user_name = update.message.reply_to_message.from_user.first_name
    elif context.args:
        arg = context.args[0]
        target_user_id, target_user_name, error = await resolve_user(context, update.effective_chat.id, arg)
        if error:
            return  # Silently fail for unfree
    
    display_name = target_user_name if target_user_name else f"User {target_user_id}"

    if target_user_id and update.effective_chat.id in group_settings:
        if "user_roles" not in group_settings[update.effective_chat.id]:
            group_settings[update.effective_chat.id]["user_roles"] = {}
        
        if str(target_user_id) in group_settings[update.effective_chat.id]["user_roles"]:
            group_settings[update.effective_chat.id]["user_roles"][str(target_user_id)]["is_free"] = False
            await save_settings(update.effective_chat.id)
            await update.message.reply_text(f"User {target_user_id} is no longer FREE.")
        else:
            await update.message.reply_text(f"User {target_user_id} was not FREE.")

async def reload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reloads group data, refreshes admin list, and shows total free members."""
    if not update.effective_chat or update.effective_chat.type == "private":
        return

    # Check admin permissions
    has_perm, error_msg = await check_admin_permissions(
        update, context, 
        required_perms=['can_change_info', 'can_restrict_members']
    )
    if not has_perm:
        await update.message.reply_text(error_msg)
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

async def resolve_user(context: ContextTypes.DEFAULT_TYPE, chat_id: int, arg: str) -> tuple:
    """
    Resolve a user from an argument (ID, username, or display name).
    
    Args:
        context: Bot context
        chat_id: Chat ID
        arg: User argument (can be ID, @username, or display name)
    
    Returns:
        tuple: (user_id, user_name, error_message)
    """
    try:
        # Try to parse as user ID first
        user_id = int(arg)
        return user_id, None, None
    except ValueError:
        # Not an ID, try to resolve as username
        if arg.startswith('@'):
            username = arg[1:]  # Remove @ symbol
        else:
            username = arg
        
        try:
            # Use get_chat to get user info by username
            # This works for public usernames
            chat_obj = await context.bot.get_chat(f"@{username}")
            
            # Check if it's a user (not a group/channel)
            if chat_obj.type == 'private':
                user_id = chat_obj.id
                user_name = chat_obj.first_name
                if chat_obj.last_name:
                    user_name += f" {chat_obj.last_name}"
                if chat_obj.username:
                    user_name += f" (@{chat_obj.username})"
                return user_id, user_name, None
            else:
                return None, None, f"❌ @{username} is not a user account."
        
        except Exception as e:
            error_str = str(e).lower()
            # If username not found, try searching in group members
            if 'not found' in error_str or 'user not found' in error_str or 'bad request' in error_str:
                try:
                    # Search through group members by display name
                    search_name = arg.lower().replace('@', '').strip()
                    
                    # Get chat members (limit to first 200 for performance)
                    admins = await context.bot.get_chat_administrators(chat_id)
                    
                    # Search in admins first
                    for admin in admins:
                        member_name = admin.user.first_name.lower()
                        if admin.user.last_name:
                            member_name += f" {admin.user.last_name.lower()}"
                        member_username = admin.user.username.lower() if admin.user.username else ""
                        
                        # Check if search term matches name or username
                        if (search_name in member_name or 
                            search_name in member_username or
                            member_name in search_name or
                            member_username in search_name):
                            
                            user_id = admin.user.id
                            user_name = admin.user.first_name
                            if admin.user.last_name:
                                user_name += f" {admin.user.last_name}"
                            if admin.user.username:
                                user_name += f" (@{admin.user.username})"
                            
                            return user_id, user_name, None
                    
                    # If not found in admins, try regular members
                    # Note: Telegram doesn't provide a direct way to get all members,
                    # so we'll return an error with helpful tips
                    return None, None, (
                        f"❌ User '{arg}' not found.\n\n"
                        f"💡 Tips:\n"
                        f"• Use the user's ID instead: /info 8016065002\n"
                        f"• Reply to their message with the command\n"
                        f"• Use their exact @username (if they have one)\n"
                        f"• Try searching with their full display name"
                    )
                except Exception as search_error:
                    return None, None, (
                        f"❌ User '{arg}' not found.\n\n"
                        f"💡 Tips:\n"
                        f"• Use the user's ID instead: /info 8016065002\n"
                        f"• Reply to their message with the command\n"
                        f"• User must have a public @username set"
                    )
            else:
                return None, None, (
                    f"❌ Could not resolve '{arg}'\n\n"
                    f"💡 Try using the user's ID or reply to their message.\n"
                    f"Error: {str(e)[:80]}"
                )


async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.type == "private":
        return
    
    # Check admin permissions
    has_perm, error_msg = await check_admin_permissions(
        update, context, 
        required_perms=['can_restrict_members']
    )
    if not has_perm:
        await update.message.reply_text(error_msg)
        return

    target_user_id = None
    target_user_name = None
    
    if update.message.reply_to_message:
        target_user_id = update.message.reply_to_message.from_user.id
        target_user_name = update.message.reply_to_message.from_user.first_name
    elif context.args:
        arg = context.args[0]
        target_user_id, target_user_name, error = await resolve_user(context, update.effective_chat.id, arg)
        if error:
            await update.message.reply_text(error)
            return
    else:
        await update.message.reply_text("Please reply to a user or provide their ID/username!")
        return
    
    if target_user_id:
        try:
            await context.bot.restrict_chat_member(
                update.effective_chat.id,
                target_user_id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                    can_change_info=True,
                    can_invite_users=True,
                    can_pin_messages=True
                )
            )
            display_name = target_user_name if target_user_name else f"User {target_user_id}"
            await update.message.reply_text(f"✅ {display_name} has been unmuted.")
        except Exception as e:
            error_msg = str(e)
            if "Chat_admin_required" in error_msg:
                await update.message.reply_text("⚠️ Error: You need ban permission to unmute users!")
            else:
                await update.message.reply_text(f"❌ Error: {error_msg}")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.type == "private":
        return
    
    # Check admin permissions
    has_perm, error_msg = await check_admin_permissions(
        update, context, 
        required_perms=['can_restrict_members']
    )
    if not has_perm:
        await update.message.reply_text(error_msg)
        return

    target_user_id = None
    target_user_name = None
    
    if update.message.reply_to_message:
        target_user_id = update.message.reply_to_message.from_user.id
        target_user_name = update.message.reply_to_message.from_user.first_name
    elif context.args:
        arg = context.args[0]
        target_user_id, target_user_name, error = await resolve_user(context, update.effective_chat.id, arg)
        if error:
            await update.message.reply_text(error)
            return
    else:
        await update.message.reply_text("Please reply to a user or provide their ID/username!")
        return

    if target_user_id:
        try:
            await context.bot.unban_chat_member(update.effective_chat.id, target_user_id, only_if_banned=True)
            display_name = target_user_name if target_user_name else f"User {target_user_id}"
            await update.message.reply_text(f"✅ {display_name} has been unbanned.")
        except Exception as e:
            error_msg = str(e)
            if "Chat_admin_required" in error_msg:
                await update.message.reply_text("⚠️ Error: You need ban permission to unban users!")
            elif "user not found" in error_msg.lower() or "PARTICIPANT_ID_INVALID" in error_msg:
                await update.message.reply_text(f"⚠️ User {target_user_id} is not banned in this group.")
            else:
                await update.message.reply_text(f"❌ Error: {error_msg}")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.type == "private":
        return
    
    # Check admin permissions
    has_perm, error_msg = await check_admin_permissions(
        update, context, 
        required_perms=['can_restrict_members']
    )
    if not has_perm:
        await update.message.reply_text(error_msg)
        return

    target_user_id = None
    target_user_name = None
    
    if update.message.reply_to_message:
        target_user_id = update.message.reply_to_message.from_user.id
        target_user_name = update.message.reply_to_message.from_user.first_name
    elif context.args:
        arg = context.args[0]
        target_user_id, target_user_name, error = await resolve_user(context, update.effective_chat.id, arg)
        if error:
            await update.message.reply_text(error)
            return
    else:
        await update.message.reply_text("Please reply to a user or provide their ID/username!")
        return

    if target_user_id:
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, target_user_id)
            display_name = target_user_name if target_user_name else f"User {target_user_id}"
            await update.message.reply_text(f"🚫 {display_name} has been banned.")
        except Exception as e:
            error_msg = str(e)
            if "Chat_admin_required" in error_msg:
                await update.message.reply_text("⚠️ Error: You need ban permission to ban users!")
            else:
                await update.message.reply_text(f"❌ Error: {error_msg}")

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.type == "private":
        return
    
    # Check admin permissions
    has_perm, error_msg = await check_admin_permissions(
        update, context, 
        required_perms=['can_restrict_members']
    )
    if not has_perm:
        await update.message.reply_text(error_msg)
        return

    target_user = None
    target_user_id = None
    target_user_mention = ""
    
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_user_id = target_user.id
        target_user_mention = target_user.mention_html()
    elif context.args:
        arg = context.args[0]
        target_user_id, target_user_name, error = await resolve_user(context, update.effective_chat.id, arg)
        if error:
            await update.message.reply_text(error)
            return
        if target_user_id:
            target_user_mention = f"<a href='tg://user?id={target_user_id}'>{target_user_name or 'User'}</a>"
    else:
        await update.message.reply_text("Please reply to a user or provide their ID/username!")
        return

    if target_user_id:
        try:
            await context.bot.restrict_chat_member(
                update.effective_chat.id,
                target_user_id,
                permissions=ChatPermissions(can_send_messages=False)
            )
            
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
    """Warn a user and show interactive buttons to manage warns."""
    if not update.effective_chat or update.effective_chat.type == "private":
        await update.message.reply_text("This command can only be used in groups!")
        return
    
    # Check admin permissions
    has_perm, error_msg = await check_admin_permissions(
        update, context,
        required_perms=['can_change_info', 'can_restrict_members']
    )
    if not has_perm:
        await update.message.reply_text(error_msg)
        return

    target_user_id = None
    target_user_name = None
    
    if update.message.reply_to_message:
        target_user_id = update.message.reply_to_message.from_user.id
        target_user_name = update.message.reply_to_message.from_user.first_name
    elif context.args:
        arg = context.args[0]
        target_user_id, target_user_name, error = await resolve_user(context, update.effective_chat.id, arg)
        if error:
            await update.message.reply_text(error)
            return
    else:
        await update.message.reply_text("Please reply to a user or provide their ID/username!")
        return
    
    if not target_user_id:
        await update.message.reply_text("Could not find the user!")
        return
    
    chat_id = update.effective_chat.id
    
    # Get current warns
    settings = await get_chat_settings(chat_id)
    user_warns = settings.get("user_warns", {}).get(str(target_user_id), 0)
    
    # Increase warn count
    user_warns += 1
    
    # Update in cache and DB
    if chat_id not in group_settings:
        group_settings[chat_id] = await get_chat_settings(chat_id)
    if "user_warns" not in group_settings[chat_id]:
        group_settings[chat_id]["user_warns"] = {}
    group_settings[chat_id]["user_warns"][str(target_user_id)] = user_warns
    await save_settings(chat_id)
    
    display_name = target_user_name if target_user_name else f"User {target_user_id}"
    
    # Check if reached max warns (3)
    punishment_msg = ""
    if user_warns >= 3:
        punishment_msg = "\n\n⚠️ User has reached maximum warns (3/3) and should be punished!"
        # Auto-reset warns after reaching max
        group_settings[chat_id]["user_warns"][str(target_user_id)] = 0
        await save_settings(chat_id)
    
    # Send warning message with interactive buttons
    text = (
        f"⚠️ <b>User Warned!</b>\n\n"
        f"👤 <b>User:</b> {display_name}\n"
        f"❗ <b>Warns:</b> {user_warns}/3{punishment_msg}"
    )
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [
        [
            InlineKeyboardButton("➖ Decrease Warn", callback_data=f"warn_decrease_{target_user_id}"),
            InlineKeyboardButton("🔄 Reset Warns", callback_data=f"warn_reset_{target_user_id}")
        ]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

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

async def block_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Add content to the custom block list.
    Usage: /block <text/word>
    This will block any message containing this text.
    """
    if not update.effective_chat or update.effective_chat.type == "private":
        await update.message.reply_text("This command can only be used in groups!")
        return
    
    # Check admin permissions
    has_perm, error_msg = await check_admin_permissions(
        update, context,
        required_perms=['can_change_info', 'can_restrict_members']
    )
    if not has_perm:
        await update.message.reply_text(error_msg)
        return
    
    # Get the text to block
    if not context.args:
        await update.message.reply_text(
            "🚫 <b>Custom Block Command</b>\n\n"
            "Usage: /block <text/word>\n\n"
            "Examples:\n"
            "• /block spam - Blocks messages containing 'spam'\n"
            "• /block http - Blocks messages with links\n"
            "• /block buy now - Blocks messages with this phrase\n\n"
            "This blocks text in ALL messages from ANYONE (including owner).",
            parse_mode='HTML'
        )
        return
    
    # Get the block text
    block_text = " ".join(context.args)
    
    # Initialize block list if not exists
    chat_id = update.effective_chat.id
    if chat_id not in group_settings:
        group_settings[chat_id] = get_default_settings()
    
    if "custom_block_list" not in group_settings[chat_id]:
        group_settings[chat_id]["custom_block_list"] = []
    
    # Check if already blocked
    if block_text.lower() in [b.lower() for b in group_settings[chat_id]["custom_block_list"]]:
        await update.message.reply_text(f"⚠️ '{block_text}' is already in the block list!")
        return
    
    # Add to block list
    group_settings[chat_id]["custom_block_list"].append(block_text)
    await save_settings(chat_id)
    
    await update.message.reply_text(
        f"✅ Added '{block_text}' to block list!\n\n"
        f"📝 All messages containing this text will be deleted automatically.\n"
        f"👥 This applies to ALL users including group owner.\n"
        f"📊 Total blocked items: {len(group_settings[chat_id]['custom_block_list'])}"
    )

async def unblock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Remove content from the custom block list.
    Usage: /unblock <text/word>
    """
    if not update.effective_chat or update.effective_chat.type == "private":
        return
    
    # Check admin permissions
    has_perm, error_msg = await check_admin_permissions(
        update, context,
        required_perms=['can_change_info', 'can_restrict_members']
    )
    if not has_perm:
        await update.message.reply_text(error_msg)
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /unblock <text/word>")
        return
    
    block_text = " ".join(context.args)
    chat_id = update.effective_chat.id
    
    if chat_id not in group_settings or "custom_block_list" not in group_settings[chat_id]:
        await update.message.reply_text("Block list is empty!")
        return
    
    # Remove from block list (case-insensitive)
    original_list = group_settings[chat_id]["custom_block_list"]
    new_list = [b for b in original_list if b.lower() != block_text.lower()]
    
    if len(new_list) == len(original_list):
        await update.message.reply_text(f"⚠️ '{block_text}' not found in block list!")
        return
    
    group_settings[chat_id]["custom_block_list"] = new_list
    await save_settings(chat_id)
    
    await update.message.reply_text(
        f"✅ Removed '{block_text}' from block list!\n"
        f"📊 Remaining blocked items: {len(new_list)}"
    )

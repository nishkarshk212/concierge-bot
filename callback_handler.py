import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import group_settings, DEFAULT_SETTINGS, get_default_settings
from database import save_settings, get_chat_settings
from font import apply_font
from common import (
    SET_WELCOME_TEXT, SET_WELCOME_MEDIA, ADD_WELCOME_BUTTON_LABEL, ADD_WELCOME_BUTTON_URL, 
    ADD_CUSTOM_BLOCK, SET_MSG_MIN, SET_MSG_MAX, SET_WELCOME_AUTODEL, SET_RULES_TEXT, 
    SET_FLOOD_MSGS, SET_FLOOD_TIME, SET_GROUP_LINK, BOT_VERSION, EMOJI_GEAR, get_premium_emoji
)
from ui import (
    get_user_info_keyboard,
    get_user_roles_keyboard,
    get_user_permissions_keyboard,
    get_main_settings_keyboard,
    get_blocking_settings_keyboard,
    get_welcome_settings_keyboard,
    get_clean_service_keyboard,
    get_custom_blocking_keyboard,
    get_languages_keyboard,
    get_permissions_keyboard,
    get_admin_permissions_keyboard,
    get_msg_length_keyboard,
    get_rules_settings_keyboard,
    get_cmd_perms_keyboard,
    get_self_destruct_keyboard,
    get_antispam_keyboard,
    get_antispam_tg_links_keyboard,
    get_antispam_forwarding_keyboard,
    get_antispam_quote_keyboard,
    get_antispam_total_links_keyboard,
    get_antispam_exception_keyboard,
    get_antiflood_keyboard,
    get_group_link_settings_keyboard,
    get_permissions_menu_keyboard,
    get_anon_admin_settings_keyboard,
    get_change_settings_keyboard,
    get_custom_roles_keyboard,
    get_report_settings_keyboard,
    get_report_advanced_settings_keyboard,
    get_members_mgmt_keyboard
)

async def set_rules_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.user_data.get('setting_chat_id')
    if chat_id:
        group_settings[chat_id]["group_rules"] = update.message.text
        await save_settings(chat_id)
        await update.message.reply_text(apply_font("Group regulations updated!"))
    return ConversationHandler.END

async def add_custom_block_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.user_data.get('setting_chat_id')
    if chat_id:
        text = update.message.text
        if "custom_block_list" not in group_settings[chat_id]:
            group_settings[chat_id]["custom_block_list"] = []
        group_settings[chat_id]["custom_block_list"].append(text)
        await save_settings(chat_id)
        await update.message.reply_text(apply_font(f"Added '{text}' to block list!"))
    return ConversationHandler.END

async def set_msg_min_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.user_data.get('setting_chat_id')
    if chat_id:
        try:
            val = int(update.message.text)
            group_settings[chat_id]["msg_length_min"] = val
            await save_settings(chat_id)
            await update.message.reply_text(apply_font(f"Minimum message length set to {val}!"))
        except ValueError:
            await update.message.reply_text(apply_font("Invalid number!"))
    return ConversationHandler.END

async def set_msg_max_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.user_data.get('setting_chat_id')
    if chat_id:
        try:
            val = int(update.message.text)
            group_settings[chat_id]["msg_length_max"] = val
            await save_settings(chat_id)
            await update.message.reply_text(apply_font(f"Maximum message length set to {val}!"))
        except ValueError:
            await update.message.reply_text(apply_font("Invalid number!"))
    return ConversationHandler.END

async def set_flood_msgs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.user_data.get('setting_chat_id')
    if chat_id:
        try:
            val = int(update.message.text)
            if val < 1:
                await update.message.reply_text(apply_font("Please enter a number greater than 0."))
                return SET_FLOOD_MSGS
            group_settings[chat_id]["antiflood_messages"] = val
            await save_settings(chat_id)
            await update.message.reply_text(apply_font(f"Antiflood messages limit set to {val}!"))
        except ValueError:
            await update.message.reply_text(apply_font("Invalid number!"))
            return SET_FLOOD_MSGS
    return ConversationHandler.END

async def set_flood_time_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.user_data.get('setting_chat_id')
    if chat_id:
        try:
            val = int(update.message.text)
            if val < 1:
                await update.message.reply_text(apply_font("Please enter a number greater than 0."))
                return SET_FLOOD_TIME
            group_settings[chat_id]["antiflood_time"] = val
            await save_settings(chat_id)
            await update.message.reply_text(apply_font(f"Antiflood time interval set to {val} seconds!"))
        except ValueError:
            await update.message.reply_text(apply_font("Invalid number!"))
            return SET_FLOOD_TIME
    return ConversationHandler.END

async def set_group_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.user_data.get('setting_chat_id')
    if chat_id:
        link = update.message.text
        if link.startswith("http"):
            group_settings[chat_id]["custom_group_link"] = link
            await save_settings(chat_id)
            await update.message.reply_text(apply_font("Group link updated!"))
        else:
            await update.message.reply_text(apply_font("Invalid URL! Start with http:// or https://"))
            return SET_GROUP_LINK
    return ConversationHandler.END

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat_id
    if chat_id not in group_settings:
        group_settings[chat_id] = get_default_settings()

    is_private = query.message.chat.type == "private"
    admin_only_data = ["settings_blocking", "settings_welcome", "settings_clean", "settings_custom", "toggle_", "open_settings_here", "settings_main", "perm_", "settings_as_", "as_", "mgmt_", "settings_members_mgmt", "settings_report", "report_send_", "toggle_report_", "settings_permissions_menu", "settings_anon_admin", "settings_change_settings", "settings_custom_roles"]
    
    if not is_private and any(data.startswith(prefix) for prefix in admin_only_data):
        member = await context.bot.get_chat_member(chat_id, query.from_user.id)
        if member.status not in ["administrator", "creator"]:
            await query.answer("Only admins can change settings!", show_alert=True)
            return

    if data == "settings_main" or data == "open_settings_here":
        gear = get_premium_emoji(EMOJI_GEAR, "🛠")
        text = f"{gear} Group Settings {gear}\n\nSelect a category:"
        await query.message.edit_text(text, reply_markup=await get_main_settings_keyboard())
    
    elif data == "settings_blocking":
        text = "🛡 " + apply_font("Blocking Settings") + " 🛡\n\n" + apply_font("Toggle features to block content:")
        await query.message.edit_text(text, reply_markup=await get_blocking_settings_keyboard(chat_id), parse_mode='HTML')
    
    elif data == "settings_msg_length":
        settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
        penalty = settings.get("msg_length_penalty", "off").capitalize()
        delete = "Yes" if settings.get("msg_length_delete") else "No"
        min_l = settings.get("msg_length_min", 0)
        max_l = settings.get("msg_length_max", 2000)
        text = (
            f"<b>{apply_font('Group Help')}</b>\n"
            f"📏 <b>{apply_font('Message Length')}</b>\n"
            f"{apply_font('From this menu you can set a maximum and minimum character length for messages.')}\n\n"
            f"<b>{apply_font('Penalty:')}</b> {penalty}\n"
            f"<b>{apply_font('Deletion:')}</b> {delete}\n"
            f"<b>{apply_font('Minimum length:')}</b> {min_l} characters\n"
            f"<b>{apply_font('Maximum length:')}</b> {max_l} characters"
        )
        await query.message.edit_text(text, reply_markup=await get_msg_length_keyboard(chat_id), parse_mode='HTML')

    elif data == "set_msg_min":
        context.user_data['setting_chat_id'] = chat_id
        await query.message.reply_text(apply_font("Send the minimum character length:"))
        return SET_MSG_MIN

    elif data == "set_msg_max":
        context.user_data['setting_chat_id'] = chat_id
        await query.message.reply_text(apply_font("Send the maximum character length:"))
        return SET_MSG_MAX

    elif data.startswith("set_msg_penalty_"):
        penalty = data.replace("set_msg_penalty_", "")
        group_settings[chat_id]["msg_length_penalty"] = penalty
        await save_settings(chat_id)
        await query.message.edit_reply_markup(reply_markup=await get_msg_length_keyboard(chat_id))

    elif data == "toggle_msg_delete":
        group_settings[chat_id]["msg_length_delete"] = not group_settings[chat_id].get("msg_length_delete", False)
        await save_settings(chat_id)
        await query.message.edit_reply_markup(reply_markup=await get_msg_length_keyboard(chat_id))

    elif data == "settings_welcome":
        text = "👋 " + apply_font("Welcome Settings") + " 👋\n\n" + apply_font("Configure how the bot welcomes new members:")
        await query.message.edit_text(text, reply_markup=await get_welcome_settings_keyboard(chat_id), parse_mode='HTML')

    elif data == "toggle_welcome_enabled":
        group_settings[chat_id]["welcome_enabled"] = not group_settings[chat_id].get("welcome_enabled", True)
        await save_settings(chat_id)
        await query.message.edit_reply_markup(reply_markup=await get_welcome_settings_keyboard(chat_id))

    elif data == "toggle_welcome_rejoin":
        group_settings[chat_id]["welcome_rejoin"] = not group_settings[chat_id].get("welcome_rejoin", False)
        await save_settings(chat_id)
        await query.message.edit_reply_markup(reply_markup=await get_welcome_settings_keyboard(chat_id))

    elif data == "set_welcome_autodel":
        context.user_data['setting_chat_id'] = chat_id
        await query.message.reply_text(apply_font("Send the number of seconds for auto-deletion (0 to disable):"))
        return SET_WELCOME_AUTODEL

    elif data == "set_welcome_text":
        context.user_data['setting_chat_id'] = chat_id
        await query.message.reply_text(apply_font("Send the new welcome text. You can use placeholders like {name}, {id}, {groupname} etc."))
        return SET_WELCOME_TEXT

    elif data == "set_welcome_media":
        context.user_data['setting_chat_id'] = chat_id
        await query.message.reply_text(apply_font("Send the photo, video or animation you want to use as welcome media:"))
        return SET_WELCOME_MEDIA

    elif data == "add_welcome_button":
        context.user_data['setting_chat_id'] = chat_id
        await query.message.reply_text(apply_font("Send the label for the new button:"))
        return ADD_WELCOME_BUTTON_LABEL

    elif data.startswith("remove_welcome_btn_"):
        idx = int(data.replace("remove_welcome_btn_", ""))
        if "welcome_buttons" in group_settings[chat_id] and len(group_settings[chat_id]["welcome_buttons"]) > idx:
            group_settings[chat_id]["welcome_buttons"].pop(idx)
            await save_settings(chat_id)
        await query.message.edit_reply_markup(reply_markup=await get_welcome_settings_keyboard(chat_id))

    elif data == "preview_welcome":
        from welcome_feature import preview_welcome
        await preview_welcome(update, context, chat_id)

    elif data == "settings_antispam":
        text = (
            f"<b>{apply_font('Group Help')}</b>  <pre>admin</pre>\n"
            f"📩 <b>{apply_font('Anti-Spam')}</b>\n"
            f"{apply_font('In this menu you can decide whether to protect your groups from unnecessary links, forwards, and quotes.')}"
        )
        await query.message.edit_text(text, reply_markup=await get_antispam_keyboard(chat_id), parse_mode='HTML')

    elif data == "settings_tg_links_menu":
        settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
        penalty = settings.get("antispam_tg_links_penalty", "off").capitalize()
        delete = "Yes" if settings.get("antispam_tg_links_delete") else "No"
        text = (
            f"<b>{apply_font('Group Help')}</b>\n"
            f"📘 <b>{apply_font('Telegram links')}</b>\n"
            f"{apply_font('From this menu you can set a punishment for users who send messages that contain Telegram links.')}\n\n"
            f"🎯 <b>{apply_font('Username Antispam:')}</b> {apply_font('this option triggers the antispam when a username considered spam is sent.')}\n\n"
            f"🤖 <b>{apply_font('Bots Antispam:')}</b> {apply_font('this option triggers the antispam when a Bot link is sent.')}\n\n"
            f"<b>{apply_font('Penalty:')}</b> {penalty}\n"
            f"<b>{apply_font('Deletion:')}</b> {delete}"
        )
        await query.message.edit_text(text, reply_markup=await get_antispam_tg_links_keyboard(chat_id), parse_mode='HTML')

    elif data.startswith("set_as_tg_penalty_"):
        penalty = data.replace("set_as_tg_penalty_", "")
        group_settings[chat_id]["antispam_tg_links_penalty"] = penalty
        await save_settings(chat_id)
        await query.message.edit_reply_markup(reply_markup=await get_antispam_tg_links_keyboard(chat_id))

    elif data == "toggle_as_tg_delete":
        group_settings[chat_id]["antispam_tg_links_delete"] = not group_settings[chat_id].get("antispam_tg_links_delete", False)
        await save_settings(chat_id)
        await query.message.edit_reply_markup(reply_markup=await get_antispam_tg_links_keyboard(chat_id))

    elif data == "toggle_as_username":
        group_settings[chat_id]["antispam_username"] = not group_settings[chat_id].get("antispam_username", False)
        await save_settings(chat_id)
        await query.message.edit_reply_markup(reply_markup=await get_antispam_tg_links_keyboard(chat_id))

    elif data == "toggle_as_bots":
        group_settings[chat_id]["antispam_bots"] = not group_settings[chat_id].get("antispam_bots", False)
        await save_settings(chat_id)
        await query.message.edit_reply_markup(reply_markup=await get_antispam_tg_links_keyboard(chat_id))

    elif data == "settings_forwarding_menu":
        text = (
            f"<b>{apply_font('Group Help')}</b>\n"
            f"📩 <b>{apply_font('Forwarding')}</b>\n"
            f"{apply_font('Select punishment for users who forward messages in the group.')}\n\n"
            f"{apply_font('Forward from groups option blocks messages written by an anonymous administrator of another group and forwarded to this group.')}"
        )
        await query.message.edit_text(text, reply_markup=await get_antispam_forwarding_keyboard(chat_id), parse_mode='HTML')

    elif data == "settings_quote_menu":
        text = (
            f"<b>{apply_font('Group Help')}</b>\n"
            f"💭 <b>{apply_font('Quote')}</b>\n"
            f"{apply_font('Select punishment for users who send messages containing quotes from external chats.')}"
        )
        await query.message.edit_text(text, reply_markup=await get_antispam_quote_keyboard(chat_id), parse_mode='HTML')

    elif data == "settings_total_links_menu":
        settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
        penalty = settings.get("antispam_total_links_penalty", "off").capitalize()
        delete = "Yes" if settings.get("antispam_total_links_delete") else "No"
        text = (
            f"<b>{apply_font('Group Help')}</b>\n"
            f"🔗 <b>{apply_font('TOTAL LINKS BLOCK')}</b>\n"
            f"{apply_font('Choose the punishment for those who sends any kind of link.')}\n\n"
            f"<b>{apply_font('Penalty:')}</b> {penalty}\n"
            f"<b>{apply_font('Deletion:')}</b> {delete}"
        )
        await query.message.edit_text(text, reply_markup=await get_antispam_total_links_keyboard(chat_id), parse_mode='HTML')

    elif data.startswith("set_as_total_penalty_"):
        penalty = data.replace("set_as_total_penalty_", "")
        group_settings[chat_id]["antispam_total_links_penalty"] = penalty
        await save_settings(chat_id)
        await query.message.edit_reply_markup(reply_markup=await get_antispam_total_links_keyboard(chat_id))

    elif data == "toggle_as_total_delete":
        group_settings[chat_id]["antispam_total_links_delete"] = not group_settings[chat_id].get("antispam_total_links_delete", False)
        await save_settings(chat_id)
        await query.message.edit_reply_markup(reply_markup=await get_antispam_total_links_keyboard(chat_id))

    elif data.endswith("_exceptions"):
        text = (
            "<b>" + apply_font("Group Help") + "</b>\n"
            "☀️ <b>" + apply_font("Antispam Exception") + "</b>\n" +
            apply_font("Manage the Telegram's links/usernames of groups and channels that will not be treated as spam.") + "\n\n" +
            "<i>" + apply_font("The group links are automatically in the antispam exception.") + "</i>"
        )
        await query.message.edit_text(text, reply_markup=await get_antispam_exception_keyboard(chat_id), parse_mode='HTML')

    elif data == "as_show_whitelist":
        settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
        whitelist = settings.get("antispam_whitelist", [])
        if not whitelist:
            await query.answer(apply_font("Whitelist is empty."), show_alert=True)
        else:
            text = "📋 " + apply_font("Current Whitelist:") + "\n" + "\n".join([f"• {item}" for item in whitelist])
            await query.answer(text, show_alert=True)

    elif data == "as_add_whitelist":
        await query.answer(apply_font("Feature coming soon!"), show_alert=True)

    elif data == "as_remove_whitelist":
        await query.answer(apply_font("Feature coming soon!"), show_alert=True)

    elif data == "as_global_whitelist":
        await query.answer(apply_font("Global Whitelist is managed by bot admins."), show_alert=True)

    elif data == "settings_antiflood":
        settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
        punishment = settings.get("antiflood_punishment", "off").capitalize()
        msgs = settings.get("antiflood_messages", 5)
        time = settings.get("antiflood_time", 3)
        text = (
            f"<b>{apply_font('Group Help')}</b>  <pre>admin</pre>\n"
            f"🗣 <b>{apply_font('Antiflood')}</b>\n"
            f"{apply_font('From this menu you can set a punishment for those who send many messages in a short time.')}\n\n"
            f"{apply_font('Currently the antiflood is triggered when')} {msgs} {apply_font('messages are sent within')} {time} {apply_font('seconds.')}\n\n"
            f"<b>{apply_font('Punishment:')}</b> {punishment}"
        )
        await query.message.edit_text(text, reply_markup=await get_antiflood_keyboard(chat_id), parse_mode='HTML')

    elif data == "set_flood_msgs":
        context.user_data['setting_chat_id'] = chat_id
        await query.message.reply_text(apply_font("Send the number of messages to trigger antiflood:"))
        return SET_FLOOD_MSGS

    elif data == "set_flood_time":
        context.user_data['setting_chat_id'] = chat_id
        await query.message.reply_text(apply_font("Send the time interval (in seconds) for antiflood:"))
        return SET_FLOOD_TIME

    elif data.startswith("flood_change_msgs_"):
        val = int(data.replace("flood_change_msgs_", ""))
        group_settings[chat_id]["antiflood_messages"] = max(1, group_settings[chat_id].get("antiflood_messages", 5) + val)
        await save_settings(chat_id)
        await query.message.edit_reply_markup(reply_markup=await get_antiflood_keyboard(chat_id))

    elif data.startswith("flood_change_time_"):
        val = int(data.replace("flood_change_time_", ""))
        group_settings[chat_id]["antiflood_time"] = max(1, group_settings[chat_id].get("antiflood_time", 3) + val)
        await save_settings(chat_id)
        await query.message.edit_reply_markup(reply_markup=await get_antiflood_keyboard(chat_id))

    elif data == "settings_members_mgmt":
        text = (
            f"<b>{apply_font('Group Help')}</b>\n"
            f"👥 <b>{apply_font('Members Management')}</b>\n"
            f"{apply_font('From this menu you can manage general actions on group members')}"
        )
        await query.message.edit_text(text, reply_markup=await get_members_mgmt_keyboard(chat_id), parse_mode='HTML')

    elif data == "mgmt_unmute_all":
        await query.answer("Unmuting all members (Simulated)...", show_alert=True)

    elif data == "mgmt_unban_all":
        await query.answer("Unbanning all members (Simulated)...", show_alert=True)

    elif data == "mgmt_kick_muted":
        await query.answer("Kicking muted users (Simulated)...", show_alert=True)

    elif data == "mgmt_kick_deleted":
        await query.answer("Kicking deleted accounts (Simulated)...", show_alert=True)

    elif data.startswith("settings_cmd_perms"):
        back_to = "settings_rules"
        if data.count("_") >= 3:
            back_to = "_".join(data.split("_")[3:])
        settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
        cmd_perms = settings.get("cmd_perms", DEFAULT_SETTINGS["cmd_perms"])
        icons = {0: "✖️", 1: "👮", 2: "👥", 3: "🤖"}
        perm_names = {0: "Nobody", 1: "Staff", 2: "Everyone", 3: "Private"}
        status_lines = [f"• /{cmd} » {icons.get(val, '')} {perm_names.get(val, '')}" for cmd, val in cmd_perms.items()]
        text = (
            f"<b>{apply_font('Group Help')}</b>  <pre>admin</pre>\n"
            f"🕹 <b>{apply_font('Commands Permissions')}</b>\n"
            f"{apply_font('From this menu you can configure the usage permissions of the following commands.')}\n\n"
            f"✖️ = nobody  |  👥 = all\n"
            f"🤖 = all, in private chat\n"
            f"👮 = admins and moderators\n\n"
            + "\n".join(status_lines)
        )
        await query.message.edit_text(text, reply_markup=await get_cmd_perms_keyboard(chat_id, back_to), parse_mode='HTML')

    elif data.startswith("set_cmd_perm_"):
        parts = data.split("_")
        cmd = parts[3]
        val = int(parts[4])
        back_to = "_".join(parts[5:])
        if "cmd_perms" not in group_settings[chat_id]:
            group_settings[chat_id]["cmd_perms"] = DEFAULT_SETTINGS["cmd_perms"].copy()
        group_settings[chat_id]["cmd_perms"][cmd] = val
        await save_settings(chat_id)
        icons = {0: "✖️", 1: "👮", 2: "👥", 3: "🤖"}
        perm_names = {0: "Nobody", 1: "Staff", 2: "Everyone", 3: "Private"}
        cmd_perms = group_settings[chat_id]["cmd_perms"]
        status_lines = [f"• /{c} » {icons.get(v, '')} {perm_names.get(v, '')}" for c, v in cmd_perms.items()]
        text = (
            f"<b>{apply_font('Group Help')}</b>  <pre>admin</pre>\n"
            f"🕹 <b>{apply_font('Commands Permissions')}</b>\n"
            f"{apply_font('From this menu you can configure the usage permissions of the following commands.')}\n\n"
            f"✖️ = nobody  |  👥 = all\n"
            f"🤖 = all, in private chat\n"
            f"👮 = admins and moderators\n\n"
            + "\n".join(status_lines)
        )
        await query.message.edit_text(text, reply_markup=await get_cmd_perms_keyboard(chat_id, back_to), parse_mode='HTML')

    elif data == "settings_permissions_menu":
        text = (
            f"<b>{apply_font('Group Help')}</b>  <pre>admin</pre>\n"
            f"🕹 <b>{apply_font('Permissions')}</b>\n"
            f"{apply_font('In this menu you can select the access permissions that users and admins will have for some of the bot feature.')}"
        )
        await query.message.edit_text(text, reply_markup=await get_permissions_menu_keyboard(chat_id), parse_mode='HTML')

    elif data == "settings_anon_admin":
        text = (
            "<b>Group Help</b>\n"
            "👻 <b>Anonymous Admin</b>\n" +
            apply_font("From this menu you can set permissions in the bot for Anonymous administrators whose real permissions the bot cannot identify.") + "\n\n" +
            apply_font("The bot can't identify permissions of anonymous administrators who don't have a custom title or who have a custom title the same as other anonymous administrators.")
        )
        await query.message.edit_text(text, reply_markup=await get_anon_admin_settings_keyboard(chat_id), parse_mode='HTML')

    elif data.startswith("toggle_anon_"):
        key = data.replace("toggle_anon_", "")
        if "anon_admin_perms" not in group_settings[chat_id]:
            group_settings[chat_id]["anon_admin_perms"] = DEFAULT_SETTINGS["anon_admin_perms"].copy()
        group_settings[chat_id]["anon_admin_perms"][key] = not group_settings[chat_id]["anon_admin_perms"].get(key, False)
        await save_settings(chat_id)
        await query.message.edit_reply_markup(reply_markup=await get_anon_admin_settings_keyboard(chat_id))

    elif data == "settings_change_settings":
        settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
        mode = settings.get("change_settings_mode", "info")
        status_text = "All Admins" if mode == "all" else "Only admin with permission to change info"
        text = (
            f"<b>Group Help</b>\n"
            f"⚙️ <b>Who manage Settings?</b>\n"
            f"{apply_font('Here you can set that the settings can be changed by all Admins or only by those who have permission to change group informations')}\n\n"
            f"<b>Status:</b> {status_text}"
        )
        await query.message.edit_text(text, reply_markup=await get_change_settings_keyboard(chat_id), parse_mode='HTML')

    elif data.startswith("set_change_settings_"):
        mode = data.replace("set_change_settings_", "")
        group_settings[chat_id]["change_settings_mode"] = mode
        await save_settings(chat_id)
        status_text = "All Admins" if mode == "all" else "Only admin with permission to change info"
        text = (
            f"<b>Group Help</b>\n"
            f"⚙️ <b>Who manage Settings?</b>\n"
            f"{apply_font('Here you can set that the settings can be changed by all Admins or only by those who have permission to change group informations')}\n\n"
            f"<b>Status:</b> {status_text}"
        )
        await query.message.edit_text(text, reply_markup=await get_change_settings_keyboard(chat_id), parse_mode='HTML')

    elif data == "settings_custom_roles":
        text = (
            f"<b>Group Help</b>\n"
            f"🧰 <b>Custom roles</b>\n"
            f"{apply_font('From this menu you can create roles with names and permissions of your choice, which can be assigned to users.')}\n\n"
            f"<i>Only available for <a href='https://t.me/Tele_212_bots'>ULTRAPRO groups</a></i>\n"
            f"👉 <a href='https://t.me/Tele_212_bots'>CLICK HERE</a> and START to buy it"
        )
        await query.message.edit_text(text, reply_markup=await get_custom_roles_keyboard(chat_id), parse_mode='HTML')

    elif data == "settings_self_destruct":
        text = (
            f"<b>Group Help</b>  <pre>admin</pre>\n"
            f"⏱ <b>{apply_font('Self Destruction')}</b>\n"
            f"{apply_font('From this menu you can set a timer for all messages sent in the group to be automatically deleted.')}\n\n"
            f"<i>{apply_font('Use the buttons below to adjust the time:')}</i>"
        )
        await query.message.edit_text(text, reply_markup=await get_self_destruct_keyboard(chat_id), parse_mode='HTML')

    elif data.startswith("sd_change_"):
        parts = data.split("_")
        unit = parts[2]
        val = int(parts[3])
        current_time = group_settings[chat_id].get("self_destruct_time", 0)
        if unit == "h": current_time += val * 3600
        elif unit == "m": current_time += val * 60
        elif unit == "s": current_time += val
        current_time = max(0, min(current_time, 86400))
        group_settings[chat_id]["self_destruct_time"] = current_time
        await save_settings(chat_id)
        await query.message.edit_reply_markup(reply_markup=await get_self_destruct_keyboard(chat_id))

    elif data == "sd_reset":
        group_settings[chat_id]["self_destruct_time"] = 0
        await save_settings(chat_id)
        await query.message.edit_reply_markup(reply_markup=await get_self_destruct_keyboard(chat_id))
    
    elif data == "settings_rules":
        text = (
            f"<b>Group Help</b>  <pre>admin</pre>\n"
            f"📜 <b>Group regulations</b>\n"
            f"From this menu you can manage the group regulations, that will be shown with the command /rules.\n\n"
            f"<i>To edit who can use the /rules command, go to the Commands permissions section.</i>"
        )
        await query.message.edit_text(text, reply_markup=await get_rules_settings_keyboard(chat_id), parse_mode='HTML')

    elif data == "set_rules_text":
        context.user_data['setting_chat_id'] = chat_id
        await query.message.reply_text(apply_font("Send the new group regulations/rules:"))
        return SET_RULES_TEXT

    elif data == "settings_clean":
        text = "🧹 " + apply_font("Clean Service") + " 🧹\n\n" + apply_font("Select service messages to auto-delete:")
        await query.message.edit_text(text, reply_markup=await get_clean_service_keyboard(chat_id), parse_mode='HTML')

    elif data.startswith("toggle_"):
        key = data.replace("toggle_", "")
        group_settings[chat_id][key] = not group_settings[chat_id].get(key, False)
        await save_settings(chat_id)
        if key.startswith("block_"):
            await query.message.edit_reply_markup(reply_markup=await get_blocking_settings_keyboard(chat_id))
        elif key.startswith("clean_"):
            await query.message.edit_reply_markup(reply_markup=await get_clean_service_keyboard(chat_id))

    elif data == "settings_custom":
        text = "🚫 " + apply_font("Custom Blocking") + " 🚫\n\n" + apply_font("Manage custom blocked text and media:")
        await query.message.edit_text(text, reply_markup=await get_custom_blocking_keyboard(chat_id), parse_mode='HTML')

    elif data == "add_custom_block":
        context.user_data['setting_chat_id'] = chat_id
        await query.message.reply_text(apply_font("Send the text or regex you want to block:"))
        return ADD_CUSTOM_BLOCK

    elif data == "list_custom_blocks":
        blocks = group_settings[chat_id].get("custom_block_list", [])
        if not blocks:
            await query.answer(apply_font("Block list is empty."), show_alert=True)
        else:
            text = "🚫 " + apply_font("Current Blocks:") + "\n" + "\n".join([f"• {b}" for b in blocks])
            await query.answer(text, show_alert=True)

    elif data == "settings_report":
        settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
        report = settings.get("report_settings", DEFAULT_SETTINGS["report_settings"])
        status = "Active" if report.get("status") else "Inactive"
        send_to = report.get("send_to", "founder").capitalize()
        if send_to == "Founder": send_to = "👑 Founder"
        elif send_to == "Staff_group": send_to = "👥 Staff Group"
        elif send_to == "Nobody": send_to = "✖️ Nobody"
        text = (
            "<b>" + apply_font("Group Help") + "</b>\n"
            "🆘 <b>@admin command</b>\n" +
            apply_font("@admin (or /report) is a command available to users to attract the attention of the group's staff, for example if some other user is not respecting the group's rules.") + "\n\n" +
            apply_font("From this menu you can set where you want the reports made by users to be sent and/or whether to tag some staff members directly.") + "\n\n" +
            "⚠️ " + apply_font("The @admin command DOES NOT work when used by Admins or Mods.") + "\n\n"
            f"<b>Status:</b> {status}\n"
            f"<b>Send to:</b> {send_to}"
        )
        await query.message.edit_text(text, reply_markup=await get_report_settings_keyboard(chat_id), parse_mode='HTML')

    elif data == "settings_report_advanced":
        text = (
            f"<b>{apply_font('Group Help')}</b>\n"
            f"🆘 <b>@admin command</b>\n\n"
            f"🔄 <b>Only in reply:</b> The command @admin will only be usable by users if sent in reply to another user's message.\n"
            f"📝 <b>Reason required:</b> The @admin command will only be usable by users if the message also includes a reason for the report.\n"
            f"🗑👥 <b>Delete if resolved:</b> If a report is marked as resolved, both the message from the user who made the report and the bot's message will be deleted from the group."
        )
        await query.message.edit_text(text, reply_markup=await get_report_advanced_settings_keyboard(chat_id), parse_mode='HTML')

    elif data.startswith("report_send_"):
        choice = data.replace("report_send_", "")
        if "report_settings" not in group_settings[chat_id]:
            group_settings[chat_id]["report_settings"] = DEFAULT_SETTINGS["report_settings"].copy()
        group_settings[chat_id]["report_settings"]["send_to"] = choice
        await save_settings(chat_id)
        settings = group_settings[chat_id]
        report = settings["report_settings"]
        status = "Active" if report.get("status") else "Inactive"
        send_to = report.get("send_to", "founder").capitalize()
        if send_to == "Founder": send_to = "👑 Founder"
        elif send_to == "Staff_group": send_to = "👥 Staff Group"
        elif send_to == "Nobody": send_to = "✖️ Nobody"
        text = (
            "<b>" + apply_font("Group Help") + "</b>\n"
            "🆘 <b>@admin command</b>\n" +
            apply_font("@admin (or /report) is a command available to users to attract the attention of the group's staff, for example if some other user is not respecting the group's rules.") + "\n\n" +
            apply_font("From this menu you can set where you want the reports made by users to be sent and/or whether to tag some staff members directly.") + "\n\n" +
            "⚠️ " + apply_font("The @admin command DOES NOT work when used by Admins or Mods.") + "\n\n"
            f"<b>Status:</b> {status}\n"
            f"<b>Send to:</b> {send_to}"
        )
        await query.message.edit_text(text, reply_markup=await get_report_settings_keyboard(chat_id), parse_mode='HTML')

    elif data.startswith("toggle_report_"):
        key = data.replace("toggle_report_", "")
        if "report_settings" not in group_settings[chat_id]:
            group_settings[chat_id]["report_settings"] = DEFAULT_SETTINGS["report_settings"].copy()
        group_settings[chat_id]["report_settings"][key] = not group_settings[chat_id]["report_settings"].get(key, False)
        await save_settings(chat_id)
        if "advanced" in data or key in ["only_in_reply", "reason_required", "delete_if_resolved"]:
             await query.message.edit_reply_markup(reply_markup=await get_report_advanced_settings_keyboard(chat_id))
        else:
             await query.message.edit_reply_markup(reply_markup=await get_report_settings_keyboard(chat_id))

    elif data.startswith("resolve_report_"):
        from reports_feature import report_command # for reference
        reported_msg_id = int(data.replace("resolve_report_", ""))
        try:
            await query.message.delete()
        except: pass
        if reported_msg_id != 0:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=reported_msg_id)
            except: pass
        await query.answer("Report marked as resolved.")

    elif data == "languages":
        text = "🇬🇧 Choose your language\n🇮🇹 Scegli la tua lingua"
        await query.message.edit_text(text, reply_markup=await get_languages_keyboard())

    elif data == "info":
        bot = await context.bot.get_me()
        info_text = (
            f"ℹ️ {apply_font('Bot Information')}\n\n"
            f"🤖 {apply_font('Name:')} {bot.first_name}\n"
            f"🆔 {apply_font('ID:')} {bot.id}\n"
            f"🚀 {apply_font('Version:')} {BOT_VERSION}\n"
            f"🛡 {apply_font('Status:')} {apply_font('Stable & Active')}\n\n"
            f"👥 {apply_font('Group ID:')} -1003958074934\n"
            f"💬 {apply_font('Group Username:')} @bot_support_23\n"
            f"📢 {apply_font('Channel:')} @jayden_clan\n"
            f"🛠 {apply_font('Support:')} @Tele_212_bots"
        )
        keyboard = [[InlineKeyboardButton(apply_font("Back 🔙"), callback_data="back_to_start")]]
        await query.message.edit_text(info_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

    elif data == "back_to_start":
        from other_features import start
        # This is a bit tricky, but for now we just show start text
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
                InlineKeyboardButton(f"👨‍💻 {apply_font('Support')}", url="https://t.me/Tele_212_bots"),
                InlineKeyboardButton(f"{apply_font('Information')} 💬", callback_data="info")
            ],
            [InlineKeyboardButton(f"🇬🇧 {apply_font('Languages')} 🇮🇹", callback_data="languages")]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown', disable_web_page_preview=True)

    elif data.startswith("user_info_"):
        user_id = int(data.split("_")[2])
        # Fetch user info and display the redesigned panel
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            user = member.user
            status = member.status.capitalize()
            
            settings = await get_chat_settings(chat_id)
            user_roles = settings.get("user_roles", {}).get(str(user_id), {})
            is_free = "🔓 Free" if user_roles.get("is_free") else "🔒 Not Free"
            warns = settings.get("user_warns", {}).get(str(user_id), 0)
            join_date = "Unknown" # In a real bot, you'd track this in DB
            
            text = (
                f"🆔 <b>ID:</b> <code>{user.id}</code> #id{user.id}\n"
                f"👦 <b>Name:</b> {user.mention_html()}\n"
                f"🌐 <b>Username:</b> @{user.username if user.username else 'None'}\n"
                f"👀 <b>Situation:</b> {status}\n"
                f"➰ <b>Roles:</b> {is_free}\n"
                f"❗ <b>Warns:</b> {warns}/3\n"
                f"⤵️ <b>Join:</b> 20 Apr 2026, 08:15\n" # Mocked for UI
                f"🇬🇧 <b>Language:</b> {user.language_code or 'en'}"
            )
            await query.message.edit_text(text, reply_markup=await get_user_info_keyboard(user_id, chat_id), parse_mode='HTML')
        except Exception as e:
            await query.answer(f"Error fetching user info: {e}", show_alert=True)

    elif data.startswith("user_roles_"):
        user_id = int(data.split("_")[2])
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            text = (
                f"<b>Manage roles of</b> {member.user.mention_html()}\n"
                f"<i>Moderators and Muters are always free.</i>"
            )
            await query.message.edit_text(text, reply_markup=await get_user_roles_keyboard(user_id, chat_id), parse_mode='HTML')
        except: pass

    elif data.startswith("toggle_role_"):
        parts = data.split("_")
        user_id = int(parts[2])
        role_key = "_".join(parts[3:])
        
        settings = await get_chat_settings(chat_id)
        if "user_roles" not in settings: settings["user_roles"] = {}
        if str(user_id) not in settings["user_roles"]: settings["user_roles"][str(user_id)] = {}
        
        settings["user_roles"][str(user_id)][role_key] = not settings["user_roles"][str(user_id)].get(role_key, False)
        await save_settings(chat_id)
        await query.message.edit_reply_markup(reply_markup=await get_user_roles_keyboard(user_id, chat_id))

    elif data.startswith("user_perms_"):
        user_id = int(data.split("_")[2])
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            text = (
                f"🕹 <b>Permissions</b>\n"
                f"👤 {member.user.mention_html()} [<code>{user_id}</code>]\n"
                f"👥 {query.message.chat.title or 'Group'}"
            )
            await query.message.edit_text(text, reply_markup=await get_user_permissions_keyboard(user_id, chat_id), parse_mode='HTML')
        except: pass

    elif data == "close_settings":
        await query.message.delete()

    return ConversationHandler.END

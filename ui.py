from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from config import group_settings, DEFAULT_SETTINGS
from font import apply_font

async def get_permissions_menu_keyboard(chat_id: int):
    """Returns the permissions menu keyboard."""
    keyboard = [
        [InlineKeyboardButton(apply_font("👻 Anonymous Admin"), callback_data="settings_anon_admin")],
        [InlineKeyboardButton(apply_font("⚙️ Change Settings"), callback_data="settings_change_settings")],
        [InlineKeyboardButton(apply_font("🧰 Custom Roles"), callback_data="settings_custom_roles")],
        [InlineKeyboardButton(apply_font("Back 🔙"), callback_data="settings_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_anon_admin_settings_keyboard(chat_id: int):
    """Returns the anonymous admin settings keyboard."""
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    anon_enabled = settings.get("anon_admin_enabled", False)
    perms = settings.get("anon_admin_perms", DEFAULT_SETTINGS["anon_admin_perms"])
    
    def get_status(key):
        status = "✅ Enable" if perms.get(key) else "❌ Disable"
        return status

    keyboard = [
        [InlineKeyboardButton(f"{'✅ Enabled' if anon_enabled else '❌ Disabled'} - Anonymous Admin", callback_data="toggle_anon_admin_master")],
        [InlineKeyboardButton(f"{get_status('ban')} {apply_font('Ban users')}", callback_data="toggle_anon_ban")],
        [InlineKeyboardButton(f"{get_status('pin')} {apply_font('Pin messages')}", callback_data="toggle_anon_pin")],
        [InlineKeyboardButton(f"{get_status('delete')} {apply_font('Delete messages')}", callback_data="toggle_anon_delete")],
        [InlineKeyboardButton(f"{get_status('add_admin')} {apply_font('Add new admins')}", callback_data="toggle_anon_add_admin")],
        [InlineKeyboardButton(apply_font("Back 🔙"), callback_data="settings_permissions_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_change_settings_keyboard(chat_id: int):
    """Returns the change settings permission keyboard."""
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    mode = settings.get("change_settings_mode", "info")
    
    all_admins_check = " ✅" if mode == "all" else ""
    only_info_check = " ✅" if mode == "info" else ""
    
    keyboard = [
        [InlineKeyboardButton(apply_font(f"All Admins{all_admins_check}"), callback_data="set_change_settings_all")],
        [InlineKeyboardButton(apply_font(f"Only Change Group info{only_info_check}"), callback_data="set_change_settings_info")],
        [InlineKeyboardButton(apply_font("Back 🔙"), callback_data="settings_permissions_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_custom_roles_keyboard(chat_id: int):
    """Returns the custom roles keyboard."""
    keyboard = [
        [InlineKeyboardButton(apply_font("💳 Buy the ULTRAPRO"), url="https://t.me/Tele_212_bots")],
        [InlineKeyboardButton(apply_font("Back 🔙"), callback_data="settings_permissions_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_user_info_keyboard(user_id: int, chat_id: int, context=None):
    """Returns the user info command keyboard with dynamic button states."""
    is_muted = False
    is_banned = False
    
    # Get user member status to determine button states
    if context:
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            
            # Check if user is muted (restricted)
            if hasattr(member, 'permissions'):
                perms = member.permissions
                if perms and not perms.can_send_messages:
                    is_muted = True
            
            # Check if user is banned
            is_banned = member.status == "kicked"
        except:
            pass
    
    # Set button text based on user status
    mute_btn_text = "🔊 Unmute" if is_muted else "🔇 Mute"
    ban_btn_text = "✅ Unban" if is_banned else "🚫 Ban"
    
    keyboard = [
        [
            InlineKeyboardButton("❗ Warns", callback_data=f"user_warns_{user_id}"),
            InlineKeyboardButton("➰ Roles", callback_data=f"user_roles_{user_id}")
        ],
        [
            InlineKeyboardButton(mute_btn_text, callback_data=f"user_mute_{user_id}"),
            InlineKeyboardButton(ban_btn_text, callback_data=f"user_ban_{user_id}")
        ],
        [InlineKeyboardButton("🕹 Permissions ↗️", callback_data=f"user_perms_{user_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_user_roles_keyboard(user_id: int, chat_id: int):
    """Returns the user roles management keyboard."""
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    user_roles = settings.get("user_roles", {}).get(str(user_id), {})
    
    def get_btn(label, key, icon):
        status = "✅" if user_roles.get(key) else "❌"
        return [
            InlineKeyboardButton(f"{icon} {label}", callback_data="noop"),
            InlineKeyboardButton(status, callback_data=f"toggle_role_{user_id}_{key}")
        ]

    keyboard = [
        get_btn("Moderator", "is_mod", "👷"),
        get_btn("Muter", "is_muter", "🙊"),
        get_btn("Chat Cleaner", "is_cleaner", "🧹"),
        get_btn("Helper", "is_helper", "⛑"),
        get_btn("Free", "is_free", "🔓"),
        [
            InlineKeyboardButton("Back 🔙", callback_data=f"user_info_{user_id}"),
            InlineKeyboardButton("Close 🔒", callback_data="close_settings")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_user_permissions_keyboard(user_id: int, chat_id: int):
    """Returns the detailed user permissions keyboard."""
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    user_perms = settings.get("user_permissions", {}).get(user_id, {})
    
    def p_btn(label, perm_key, status=None):
        # If status not provided, get it from user_perms
        if status is None:
            status = user_perms.get(perm_key, False)
        icon_status = "✅" if status else "❌"
        return InlineKeyboardButton(f"{icon_status} {label}", callback_data=f"toggle_perm_{user_id}_{perm_key}")

    keyboard = [
        [p_btn("Text messages", "block_text")],
        [p_btn("Photo", "block_media"), p_btn("Video", "block_video")],
        [p_btn("Sticker/GIF", "block_stickers"), p_btn("Audio", "block_audio")],
        [p_btn("Voice", "block_voice"), p_btn("File", "block_documents")],
        [p_btn("Round Video", "block_video_note"), p_btn("Polls", "block_poll")],
        [p_btn("Enable link previews", "block_link")],
        [p_btn("Edit own tag", "block_embed_link", False)],
        [
            InlineKeyboardButton("Save ✔️", callback_data=f"user_info_{user_id}"),
            InlineKeyboardButton("Close 🔒", callback_data="close_settings")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_main_settings_keyboard():
    """Returns the main settings menu keyboard optimized for mobile."""
    keyboard = [
        [
            InlineKeyboardButton(apply_font("🔐 Blocks"), callback_data="settings_blocking"),
            InlineKeyboardButton(apply_font("📏 Msg Length"), callback_data="settings_msg_length")
        ],
        [
            InlineKeyboardButton(apply_font("👋 Welcome"), callback_data="settings_welcome"),
            InlineKeyboardButton(apply_font("📜 Rules"), callback_data="settings_rules")
        ],
        [
            InlineKeyboardButton(apply_font("⏱ Auto-Delete"), callback_data="settings_self_destruct"),
            InlineKeyboardButton(apply_font("🛡 Anti-Spam"), callback_data="settings_antispam")
        ],
        [
            InlineKeyboardButton(apply_font("🗣 Antiflood"), callback_data="settings_antiflood"),
            InlineKeyboardButton(apply_font("🔗 Group Link"), callback_data="settings_link")
        ],
        [
            InlineKeyboardButton(apply_font("🕹 Permissions"), callback_data="settings_permissions_menu"),
            InlineKeyboardButton(apply_font("👥 Members"), callback_data="settings_members_mgmt")
        ],
        [
            InlineKeyboardButton(apply_font("🧹 Cleaner"), callback_data="settings_clean"),
            InlineKeyboardButton(apply_font("🚫 Custom Block"), callback_data="settings_custom")
        ],
        [
            InlineKeyboardButton(apply_font("🆘 @admin"), callback_data="settings_report"),
            InlineKeyboardButton(apply_font("🛡️ Bot Protect"), callback_data="settings_bot_protection")
        ],
        [
            InlineKeyboardButton(apply_font("🔄 Recurring Msg"), callback_data="settings_recurring"),
            InlineKeyboardButton(apply_font("❌ Close"), callback_data="close_settings")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_blocking_settings_keyboard(chat_id: int):
    """Returns the blocking settings keyboard."""
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    
    # List of blocking features
    features = [
        ("Stickers", "block_stickers"),
        ("Media", "block_media"),
        ("Documents", "block_documents"),
        ("🎵 Music", "block_audio"),
        ("Forward", "block_forward"),
        ("Command", "block_command"),
        ("Premium Sticker", "block_premium_sticker"),
        ("Channel Post", "block_channel_post"),
        ("Contact", "block_contact"),
        ("Location", "block_location"),
        ("Voice", "block_voice"),
        ("Video Note", "block_video_note"),
        ("Poll", "block_poll"),
        ("Embed Link", "block_embed_link"),
        ("Link", "block_link"),
    ]
    
    keyboard = []
    # Two columns
    for i in range(0, len(features), 2):
        row = []
        for j in range(2):
            if i + j < len(features):
                label, key = features[i + j]
                status = "✅" if settings.get(key) else "❌"
                row.append(InlineKeyboardButton(f"{status} {apply_font(label)}", callback_data=f"toggle_{key}"))
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton(apply_font("Back 🔙"), callback_data="settings_main")])
    return InlineKeyboardMarkup(keyboard)

async def get_welcome_settings_keyboard(chat_id: int):
    """Returns the welcome settings keyboard with button management."""
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    status = "✅ Enabled" if settings.get("welcome_enabled") else "❌ Disabled"
    rejoin_status = "✅ Enabled" if settings.get("welcome_rejoin") else "❌ Disabled"
    autodel = settings.get("welcome_autodelete", 0)
    autodel_text = f"⏱ {autodel}s" if autodel > 0 else "❌ Off"
    buttons = settings.get("welcome_buttons", [])
    
    keyboard = [
        [InlineKeyboardButton(apply_font(f"Status: {status}"), callback_data="toggle_welcome_enabled")],
        [InlineKeyboardButton(apply_font(f"Welcome Rejoin: {rejoin_status}"), callback_data="toggle_welcome_rejoin")],
        [InlineKeyboardButton(apply_font(f"Auto Delete: {autodel_text}"), callback_data="set_welcome_autodel")],
        [InlineKeyboardButton(apply_font("Set Welcome Text 📝"), callback_data="set_welcome_text")],
        [InlineKeyboardButton(apply_font("Set Welcome Media 🖼"), callback_data="set_welcome_media")],
        [InlineKeyboardButton(apply_font("Add Inline Button ➕"), callback_data="add_welcome_button")]
    ]
    
    # List added buttons for removal
    if buttons:
        keyboard.append([InlineKeyboardButton(apply_font("--- Added Buttons (Click to Remove) ---"), callback_data="noop")])
        for idx, btn in enumerate(buttons):
            keyboard.append([InlineKeyboardButton(f"🗑 {btn['label']}", callback_data=f"remove_welcome_btn_{idx}")])
    
    keyboard.append([InlineKeyboardButton(apply_font("Preview Welcome 👀"), callback_data="preview_welcome")])
    keyboard.append([InlineKeyboardButton(apply_font("Back 🔙"), callback_data="settings_main")])
    return InlineKeyboardMarkup(keyboard)

async def get_report_settings_keyboard(chat_id: int):
    """Returns the @admin command settings keyboard."""
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    report = settings.get("report_settings", DEFAULT_SETTINGS["report_settings"])
    
    status = "Active" if report.get("status") else "Inactive"
    send_to = report.get("send_to", "founder").capitalize()
    if send_to == "Founder": send_to = "👑 Founder"
    elif send_to == "Staff_group": send_to = "👥 Staff Group"
    elif send_to == "Nobody": send_to = "✖️ Nobody"

    tag_founder = "✅" if report.get("tag_founder") else "❌"
    tag_admins = "✅" if report.get("tag_admins") else "❌"

    keyboard = [
        [
            InlineKeyboardButton(f"✖️ Nobody", callback_data="report_send_nobody"),
            InlineKeyboardButton(f"👑 Founder", callback_data="report_send_founder")
        ],
        [InlineKeyboardButton(f"👥 Staff Group", callback_data="report_send_staff_group")],
        [InlineKeyboardButton(f"🔔 Tag Founder {tag_founder}", callback_data="toggle_report_tag_founder")],
        [InlineKeyboardButton(f"🔔 Tag Admins {tag_admins}", callback_data="toggle_report_tag_admins")],
        [InlineKeyboardButton(f"🛠 Advanced settings 🆕", callback_data="settings_report_advanced")],
        [InlineKeyboardButton(f"🔙 Back", callback_data="settings_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_report_advanced_settings_keyboard(chat_id: int):
    """Returns the @admin advanced settings keyboard."""
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    report = settings.get("report_settings", DEFAULT_SETTINGS["report_settings"])
    
    only_reply = "✅" if report.get("only_in_reply") else "❌"
    reason_req = "✅" if report.get("reason_required") else "❌"
    del_resolved = "✅" if report.get("delete_if_resolved") else "❌"

    keyboard = [
        [InlineKeyboardButton(f"🔄 Only in reply {only_reply}", callback_data="toggle_report_only_in_reply")],
        [InlineKeyboardButton(f"📝 Reason required {reason_req}", callback_data="toggle_report_reason_required")],
        [InlineKeyboardButton(f"🗑👥 Delete if resolved {del_resolved}", callback_data="toggle_report_delete_if_resolved")],
        [InlineKeyboardButton(f"🔙 Back", callback_data="settings_report")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_rules_settings_keyboard(chat_id: int):
    """Returns the group regulations settings keyboard."""
    keyboard = [
        [InlineKeyboardButton("✍️ Customize message", callback_data="set_rules_text")],
        [InlineKeyboardButton("Back 🔙", callback_data="settings_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_cmd_perms_keyboard(chat_id: int, back_to: str = "settings_rules"):
    """Returns the command permissions keyboard."""
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    cmd_perms = settings.get("cmd_perms", DEFAULT_SETTINGS["cmd_perms"])
    
    # 0: nobody (✖️), 1: staff (👮), 2: everyone (👥), 3: private (🤖)
    icons = {0: "✖️", 1: "👮", 2: "👥", 3: "🤖"}
    
    keyboard = []
    commands = ["staff", "rules", "me", "translate", "link"]
    
    for cmd in commands:
        current_val = cmd_perms.get(cmd, 2)
        row = [InlineKeyboardButton(f"/{cmd}", callback_data="noop")]
        for val in range(4):
            icon = icons[val]
            row.append(InlineKeyboardButton(icon, callback_data=f"set_cmd_perm_{cmd}_{val}_{back_to}"))
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton(apply_font("Back 🔙"), callback_data=back_to)])
    return InlineKeyboardMarkup(keyboard)

async def get_clean_service_keyboard(chat_id: int):
    """Returns the clean service settings keyboard."""
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    
    features = [
        ("Join", "clean_join"),
        ("Left", "clean_left"),
        ("Voice Start", "clean_voice_start"),
        ("Voice End", "clean_voice_end"),
        ("Voice Schedule", "clean_voice_schedule"),
        ("Voice Invite", "clean_voice_invite"),
        ("Pinned Msg", "clean_pinned"),
    ]
    
    keyboard = []
    for i in range(0, len(features), 2):
        row = []
        for j in range(2):
            if i + j < len(features):
                label, key = features[i + j]
                status = "✅" if settings.get(key) else "❌"
                row.append(InlineKeyboardButton(f"{status} {apply_font(label)}", callback_data=f"toggle_{key}"))
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton(apply_font("Back 🔙"), callback_data="settings_main")])
    return InlineKeyboardMarkup(keyboard)

async def get_self_destruct_keyboard(chat_id: int):
    """Returns the self-destruction settings keyboard."""
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    sd_time = settings.get("self_destruct_time", 0)
    sd_enabled = sd_time > 0
    
    # Convert seconds to H:M:S
    h = sd_time // 3600
    m = (sd_time % 3600) // 60
    s = sd_time % 60
    
    keyboard = [
        [InlineKeyboardButton(f"{'✅ Enabled' if sd_enabled else '❌ Disabled'} - Self Destruction", callback_data="toggle_sd_master")],
        [
            InlineKeyboardButton("H +", callback_data="sd_change_h_1"),
            InlineKeyboardButton("M +", callback_data="sd_change_m_1"),
            InlineKeyboardButton("S +", callback_data="sd_change_s_1")
        ],
        [
            InlineKeyboardButton(f"{h:02d}h", callback_data="noop"),
            InlineKeyboardButton(f"{m:02d}m", callback_data="noop"),
            InlineKeyboardButton(f"{s:02d}s", callback_data="noop")
        ],
        [
            InlineKeyboardButton("H -", callback_data="sd_change_h_-1"),
            InlineKeyboardButton("M -", callback_data="sd_change_m_-1"),
            InlineKeyboardButton("S -", callback_data="sd_change_s_-1")
        ],
        [InlineKeyboardButton("Reset 🔄", callback_data="sd_reset")],
        [InlineKeyboardButton(apply_font("Back 🔙"), callback_data="settings_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_custom_blocking_keyboard(chat_id: int):
    """Returns the custom blocking settings keyboard."""
    keyboard = [
        [InlineKeyboardButton(apply_font("Add Text/Regex Block ➕"), callback_data="add_custom_block")],
        [InlineKeyboardButton(apply_font("List Current Blocks 📜"), callback_data="list_custom_blocks")],
        [InlineKeyboardButton(apply_font("Back 🔙"), callback_data="settings_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_permissions_keyboard(chat_id: int, user_id: int):
    """Returns the user permissions (free system) keyboard."""
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    user_perms = settings.get("user_permissions", {}).get(user_id, {})
    
    features = [
        ("Stickers", "block_stickers"),
        ("Media", "block_media"),
        ("Documents", "block_documents"),
        ("Forward", "block_forward"),
        ("Command", "block_command"),
        ("Premium Sticker", "block_premium_sticker"),
        ("Channel Post", "block_channel_post"),
        ("Contact", "block_contact"),
        ("Location", "block_location"),
        ("Voice", "block_voice"),
        ("Video Note", "block_video_note"),
        ("Poll", "block_poll"),
        ("Embed Link", "block_embed_link"),
        ("Link", "block_link"),
    ]
    
    keyboard = []
    for i in range(0, len(features), 2):
        row = []
        for j in range(2):
            if i + j < len(features):
                label, key = features[i + j]
                # In perms menu, ✅ means they ARE freed (allowed), ❌ means they are NOT freed (blocked)
                status = "✅" if user_perms.get(key, False) else "❌"
                row.append(InlineKeyboardButton(f"{status} {apply_font(label)}", callback_data=f"perm_{user_id}_{key}"))
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton(apply_font("Close 🔒"), callback_data="close_settings")])
    return InlineKeyboardMarkup(keyboard)

async def get_msg_length_keyboard(chat_id: int):
    """Returns the message length settings keyboard."""
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    penalty = settings.get("msg_length_penalty", "off")
    delete = settings.get("msg_length_delete", False)
    
    def get_penalty_btn(label, p_type):
        icon = "✅" if penalty == p_type else "❌"
        return InlineKeyboardButton(f"{icon} {label}", callback_data=f"set_msg_penalty_{p_type}")

    keyboard = [
        [get_penalty_btn("Off", "off"), get_penalty_btn("Warn", "warn"), get_penalty_btn("Kick", "kick")],
        [get_penalty_btn("Mute", "mute"), get_penalty_btn("Ban", "ban")],
        [InlineKeyboardButton(f"🗑 Delete Messages {'✅' if delete else '❌'}", callback_data="toggle_msg_length_delete")],
        [InlineKeyboardButton(apply_font("📏 Minimum length"), callback_data="set_msg_min")],
        [InlineKeyboardButton(apply_font("📏 Maximum length"), callback_data="set_msg_max")],
        [InlineKeyboardButton(apply_font("Back 🔙"), callback_data="settings_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_admin_permissions_keyboard(user_id: int, current_perms: dict):
    """Returns the admin permissions keyboard matching the user's UI image."""
    
    def get_btn(label, key):
        status = "✅" if current_perms.get(key, False) else "❌"
        return InlineKeyboardButton(f"{status} {label}", callback_data=f"adm_perm_{user_id}_{key}")

    keyboard = [
        [get_btn("Change group info", "can_change_info")],
        [get_btn("Ban users", "can_ban_users"), get_btn("Delete messages", "can_delete_messages")],
        [get_btn("Add members", "can_invite_users"), get_btn("Pin messages", "can_pin_messages")],
        [get_btn("Post stories", "can_post_stories")],
        [get_btn("Edit stories", "can_edit_stories"), get_btn("Delete stories", "can_delete_stories")],
        [get_btn("Manage video chats", "can_manage_video_chats")],
        [get_btn("Manage topics", "can_manage_topics")],
        [get_btn("Edit member tags", "can_promote_members")],
        [get_btn("Add new admins", "can_promote_members")],
        [InlineKeyboardButton(f"{'🔒' if current_perms.get('is_anonymous', False) else '🔓'} Anonymous Admin", callback_data=f"adm_perm_{user_id}_is_anonymous")],
        [get_btn("Mute users", "can_mute_users")],
        [InlineKeyboardButton("Save ✔️", callback_data=f"adm_save_{user_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_languages_keyboard():
    """Returns the language selection keyboard based on the provided image."""
    langs = [
        ("Italiano", "it"), ("Español", "es"),
        ("Português", "pt"), ("Deutsch", "de"),
        ("Français", "fr"), ("Română", "ro"),
        ("Nederlands", "nl"), ("Türkçe", "tr"),
        ("简体中文", "zh-CN"), ("繁體中文", "zh-TW"),
        ("Українська", "uk"), ("Русский", "ru"),
        ("Қазақ", "kk"), ("Indonesia", "id"),
        ("O'zbekcha", "uz"), ("Ўзбекча", "uz-cy"),
        ("Azərbaycanca", "az"), ("Melayu", "ms"),
        ("Soomaali", "so"), ("Shqipe", "sq"),
        ("Srpski", "sr"), ("Amharic", "am"),
        ("Ελληνικά", "el"), ("العربية", "ar"),
        ("한국어", "ko"), ("پارسی", "fa"),
        ("کوردی", "ku"), ("हिंदी", "hi"),
        ("සිංහල", "si"), ("বাংলা", "bn"),
        ("اردو", "ur"), ("עברית", "he")
    ]
    
    keyboard = [[InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]]
    for i in range(0, len(langs), 2):
        row = [
            InlineKeyboardButton(langs[i][0], callback_data=f"lang_{langs[i][1]}"),
            InlineKeyboardButton(langs[i+1][0], callback_data=f"lang_{langs[i+1][1]}")
        ]
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_start")])
    return InlineKeyboardMarkup(keyboard)

async def get_antispam_keyboard(chat_id: int):
    """Returns the anti-spam settings keyboard."""
    keyboard = [
        [InlineKeyboardButton("📘 Telegram links", callback_data="settings_tg_links_menu")],
        [InlineKeyboardButton("💭 Quote", callback_data="settings_quote_menu")],
        [InlineKeyboardButton("🔗 Total links block", callback_data="settings_total_links_menu")],
        [InlineKeyboardButton("🔙 Back", callback_data="settings_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_antispam_tg_links_keyboard(chat_id: int):
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    penalty = settings.get("antispam_tg_links_penalty", "off")
    delete = settings.get("antispam_tg_links_delete", False)
    username = settings.get("antispam_username", False)
    bots = settings.get("antispam_bots", False)

    def get_penalty_btn(label, p_type):
        icon = "❌" if penalty == p_type else ""
        if p_type == "off" and penalty == "off": icon = "❌"
        elif p_type == "warn" and penalty == "warn": icon = "❗"
        elif p_type == "kick" and penalty == "kick": icon = "❗"
        elif p_type == "mute" and penalty == "mute": icon = "🔇"
        elif p_type == "ban" and penalty == "ban": icon = "🚫"
        else: icon = ""
        
        # Based on screenshot: Off has X, Warn has !, Kick has !, Mute has speaker, Ban has ban icon
        display_icon = ""
        if p_type == "off": display_icon = "❌ "
        elif p_type == "warn": display_icon = "❗ "
        elif p_type == "kick": display_icon = "❗ "
        elif p_type == "mute": display_icon = "🔇 "
        elif p_type == "ban": display_icon = "🚫 "

        is_active = (penalty == p_type)
        prefix = display_icon if is_active else ""
        return InlineKeyboardButton(f"{prefix}{label}", callback_data=f"set_as_tg_penalty_{p_type}")

    keyboard = [
        [get_penalty_btn("Off", "off"), get_penalty_btn("Warn", "warn"), get_penalty_btn("Kick", "kick")],
        [get_penalty_btn("Mute", "mute"), get_penalty_btn("Ban", "ban")],
        [InlineKeyboardButton(f"🗑 Delete Messages {'✅' if delete else '❌'}", callback_data="toggle_as_tg_delete")],
        [InlineKeyboardButton(f"🎯 Username Antispam {'✅' if username else '❌'}", callback_data="toggle_as_username")],
        [InlineKeyboardButton(f"🤖 Bots Antispam {'✅' if bots else '❌'}", callback_data="toggle_as_bots")],
        [
            InlineKeyboardButton("🔙 Back", callback_data="settings_antispam"),
            InlineKeyboardButton("☀️ Exceptions", callback_data="as_tg_exceptions")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_antispam_forwarding_keyboard(chat_id: int):
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    
    keyboard = [
        [InlineKeyboardButton(f"📣 Channels", callback_data="set_as_fwd_chan"), InlineKeyboardButton(f"👥 Groups", callback_data="set_as_fwd_group")],
        [InlineKeyboardButton(f"👤 Users", callback_data="set_as_fwd_user"), InlineKeyboardButton(f"🤖 Bots", callback_data="set_as_fwd_bot")],
        [
            InlineKeyboardButton("🔙 Back", callback_data="settings_antispam"),
            InlineKeyboardButton("☀️ Exceptions", callback_data="as_fwd_exceptions")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_antispam_quote_keyboard(chat_id: int):
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    penalty = settings.get("antispam_quote_penalty", "off")
    delete = settings.get("antispam_quote_delete", False)

    def get_penalty_btn(label, p_type):
        display_icon = ""
        if p_type == "off": display_icon = "❌ "
        elif p_type == "warn": display_icon = "❗ "
        elif p_type == "kick": display_icon = "❗ "
        elif p_type == "mute": display_icon = "🔇 "
        elif p_type == "ban": display_icon = "🚫 "

        is_active = (penalty == p_type)
        prefix = display_icon if is_active else ""
        return InlineKeyboardButton(f"{prefix}{label}", callback_data=f"set_as_quote_penalty_{p_type}")

    keyboard = [
        [get_penalty_btn("Off", "off"), get_penalty_btn("Warn", "warn"), get_penalty_btn("Kick", "kick")],
        [get_penalty_btn("Mute", "mute"), get_penalty_btn("Ban", "ban")],
        [InlineKeyboardButton(f"🗑 Delete Messages {'✅' if delete else '❌'}", callback_data="toggle_as_quote_delete")],
        [
            InlineKeyboardButton("🔙 Back", callback_data="settings_antispam"),
            InlineKeyboardButton("☀️ Exceptions", callback_data="as_quote_exceptions")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_antispam_total_links_keyboard(chat_id: int):
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    penalty = settings.get("antispam_total_links_penalty", "off")
    delete = settings.get("antispam_total_links_delete", False)

    def get_penalty_btn(label, p_type):
        display_icon = ""
        if p_type == "off": display_icon = "❌ "
        elif p_type == "warn": display_icon = "❗ "
        elif p_type == "kick": display_icon = "❗ "
        elif p_type == "mute": display_icon = "🔇 "
        elif p_type == "ban" and penalty == "ban": display_icon = "🚫 "

        is_active = (penalty == p_type)
        prefix = display_icon if is_active else ""
        return InlineKeyboardButton(f"{prefix}{label}", callback_data=f"set_as_total_penalty_{p_type}")

    keyboard = [
        [get_penalty_btn("Off", "off"), get_penalty_btn("Warn", "warn"), get_penalty_btn("Kick", "kick")],
        [get_penalty_btn("Mute", "mute"), get_penalty_btn("Ban", "ban")],
        [InlineKeyboardButton(f"🗑 Delete Messages {'✅' if delete else '❌'}", callback_data="toggle_as_total_delete")],
        [
            InlineKeyboardButton("🔙 Back", callback_data="settings_antispam"),
            InlineKeyboardButton("☀️ Exceptions", callback_data="as_total_exceptions")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_antispam_exception_keyboard(chat_id: int):
    """Returns the antispam exception settings keyboard."""
    keyboard = [
        [InlineKeyboardButton(apply_font("🔤 Show Whitelist"), callback_data="as_show_whitelist")],
        [
            InlineKeyboardButton(apply_font("➕ Add"), callback_data="as_add_whitelist"),
            InlineKeyboardButton(apply_font("➖ Remove"), callback_data="as_remove_whitelist")
        ],
        [InlineKeyboardButton(apply_font("🌐 Global Whitelist"), callback_data="as_global_whitelist")],
        [InlineKeyboardButton(apply_font("Back 🔙"), callback_data="settings_antispam")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_antiflood_keyboard(chat_id: int):
    """Returns the antiflood settings keyboard with +/- buttons."""
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    punishment = settings.get("antiflood_punishment", "off")
    delete = settings.get("antiflood_delete", False)
    msgs = settings.get("antiflood_messages", 5)
    time = settings.get("antiflood_time", 3)
    warn_limit = settings.get("antiflood_warn_limit", 3)
    
    keyboard = [
        [
            InlineKeyboardButton("📄 Msgs +", callback_data="flood_change_msgs_1"),
            InlineKeyboardButton("📄 Msgs -", callback_data="flood_change_msgs_-1")
        ],
        [
            InlineKeyboardButton("🕒 Time +", callback_data="flood_change_time_1"),
            InlineKeyboardButton("🕒 Time -", callback_data="flood_change_time_-1")
        ],
        [
            InlineKeyboardButton(f"📄 {msgs} messages", callback_data="noop"),
            InlineKeyboardButton(f"🕒 {time} seconds", callback_data="noop")
        ],
        [
            InlineKeyboardButton("⚠️ Warn +", callback_data="flood_change_warn_1"),
            InlineKeyboardButton("⚠️ Warn -", callback_data="flood_change_warn_-1")
        ],
        [InlineKeyboardButton(f"⚠️ {warn_limit} warnings before punishment", callback_data="noop")],
        [
            InlineKeyboardButton(f"{'✅' if punishment == 'off' else ''} Off", callback_data="set_flood_off"),
            InlineKeyboardButton(f"{'✅' if punishment == 'warn' else ''} Warn", callback_data="set_flood_warn")
        ],
        [
            InlineKeyboardButton(f"{'✅' if punishment == 'kick' else ''} Kick", callback_data="set_flood_kick"),
            InlineKeyboardButton(f"{'✅' if punishment == 'mute' else ''} Mute", callback_data="set_flood_mute"),
            InlineKeyboardButton(f"{'✅' if punishment == 'ban' else ''} Ban", callback_data="set_flood_ban")
        ],
        [InlineKeyboardButton(f"🗑 Delete Messages {'✔️' if delete else ''}", callback_data="toggle_flood_delete")],
        [InlineKeyboardButton("🔙 Back", callback_data="settings_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_members_mgmt_keyboard(chat_id: int):
    """Returns the members management keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🔇 Unmute all", callback_data="mgmt_unmute_all"),
            InlineKeyboardButton("🚫 Unban all", callback_data="mgmt_unban_all")
        ],
        [InlineKeyboardButton("❗ Kick muted/restricted users", callback_data="mgmt_kick_muted")],
        [InlineKeyboardButton("💀 Kick deleted accounts", callback_data="mgmt_kick_deleted")],
        [InlineKeyboardButton("🔙 Back", callback_data="settings_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_bot_protection_keyboard(chat_id: int):
    """Returns the bot protection settings keyboard."""
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    enabled = settings.get("bot_protection_enabled", False)
    status = "✅ Enabled" if enabled else "❌ Disabled"
    
    keyboard = [
        [InlineKeyboardButton(f"Status: {status}", callback_data="toggle_bot_protection")],
        [InlineKeyboardButton("🔙 Back", callback_data="settings_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_group_link_settings_keyboard(chat_id: int):
    """Returns the group link settings keyboard."""
    keyboard = [
        [InlineKeyboardButton("✍️ Set", callback_data="set_group_link")],
        [InlineKeyboardButton("🔙 Back", callback_data="settings_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_permissions_menu_keyboard(chat_id: int):
    """Returns the permissions menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("🕹 Commands Permissions", callback_data="settings_cmd_perms_settings_permissions_menu")],
        [InlineKeyboardButton("👻 Anonymous Admin", callback_data="settings_anon_admin")],
        [InlineKeyboardButton("⚙️ Change settings", callback_data="settings_change_settings")],
        [InlineKeyboardButton("🧰 Custom roles 🆕", callback_data="settings_custom_roles")],
        [InlineKeyboardButton("🔙 Back", callback_data="settings_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_recurring_messages_keyboard(chat_id: int):
    """Returns the recurring messages settings keyboard."""
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    recurring = settings.get("recurring_messages", DEFAULT_SETTINGS["recurring_messages"])
    
    enabled = recurring.get("enabled", False)
    enabled_status = "✅ Enabled" if enabled else "❌ Disabled"
    
    msg_type = recurring.get("message_type", "text")
    type_icons = {
        "text": "📝",
        "photo": "🖼",
        "video": "🎥",
        "animation": "🎬"
    }
    type_status = f"{type_icons.get(msg_type, '📝')} {msg_type.capitalize()}"
    
    interval_minutes = recurring.get("interval_minutes", 5)
    interval_hours = recurring.get("interval_hours", 0)
    
    buttons = recurring.get("message_buttons", [])
    buttons_count = len(buttons)
    
    keyboard = [
        [InlineKeyboardButton(f"Status: {enabled_status}", callback_data="toggle_recurring_enabled")],
        [InlineKeyboardButton(f"Message Type: {type_status}", callback_data="noop")],
        [
            InlineKeyboardButton("📝 Text", callback_data="set_recurring_type_text"),
            InlineKeyboardButton("🖼 Photo", callback_data="set_recurring_type_photo")
        ],
        [
            InlineKeyboardButton("🎥 Video", callback_data="set_recurring_type_video"),
            InlineKeyboardButton("🎬 GIF", callback_data="set_recurring_type_animation")
        ],
        [InlineKeyboardButton("✍️ Set Message Text", callback_data="set_recurring_text")],
        [InlineKeyboardButton("🖼 Set Message Media", callback_data="set_recurring_media")],
        [InlineKeyboardButton(f"➕ Add Button ({buttons_count})", callback_data="add_recurring_button")],
    ]
    
    # Show added buttons for removal
    if buttons:
        keyboard.append([InlineKeyboardButton("--- Buttons (Click to Remove) ---", callback_data="noop")])
        for idx, btn in enumerate(buttons):
            keyboard.append([InlineKeyboardButton(f"🗑 {btn['label']}", callback_data=f"remove_recurring_btn_{idx}")])
    
    # Interval settings
    keyboard.append([InlineKeyboardButton("--- Time Interval ---", callback_data="noop")])
    
    # Hours row
    if interval_hours > 0:
        keyboard.append([
            InlineKeyboardButton("Hours +", callback_data="recurring_interval_hours_1"),
            InlineKeyboardButton("Hours -", callback_data="recurring_interval_hours_-1")
        ])
    
    # Minutes row
    keyboard.append([
        InlineKeyboardButton("Minutes +", callback_data="recurring_interval_minutes_1"),
        InlineKeyboardButton("Minutes -", callback_data="recurring_interval_minutes_-1")
    ])
    
    # Display current interval
    interval_text = []
    if interval_hours > 0:
        interval_text.append(f"{interval_hours}h")
    if interval_minutes > 0 or interval_hours == 0:
        interval_text.append(f"{interval_minutes}m")
    keyboard.append([InlineKeyboardButton(f"⏱ { ' '.join(interval_text)}", callback_data="noop")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="settings_main")])
    
    return InlineKeyboardMarkup(keyboard)

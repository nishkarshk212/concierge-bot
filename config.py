import os
import copy
from dotenv import load_dotenv

load_dotenv()

# Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "8409128631:AAGg9_TZ63BglZCQK0IEoS2HF9NmEYqo-UM")

# MongoDB URI
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://lilyy67u_db_user:Nishkarsh123@grouphelp2.06f2yus.mongodb.net/?appName=Grouphelp2")

# Log Group ID
LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", "-1003757375746"))

# In-memory storage (fallback/cache)
group_settings = {}

DEFAULT_SETTINGS = {
    # Blocking Section
    "block_stickers": False,
    "block_media": False,
    "block_documents": False,
    "block_forward": False,
    "block_command": False,
    "block_premium_sticker": False,
    "block_channel_post": False,
    "block_contact": False,
    "block_location": False,
    "block_voice": False,
    "block_video_note": False,
    "block_poll": False,
    "block_dice": False, # New
    "block_game": False, # New
    "block_audio": False, # New
    "block_embed_link": False,
    "block_link": False,
    
    # Welcome Settings
    "welcome_text": "Welcome to our group!",
    "welcome_media": None, # file_id
    "welcome_media_type": None,
    "welcome_buttons": [], # list of dicts {'label': '...', 'url': '...'}
    "welcome_enabled": True,
    "welcome_rejoin": False, # New: welcome users who left and came back
    "welcome_autodelete": 0, # New: 0 means off, otherwise time in seconds
    "seen_users": [], # New: list of user IDs who have joined before

    # Clean Service
    "clean_join": False,
    "clean_left": False,
    "clean_title": False, # New
    "clean_photo": False, # New
    "clean_voice_start": False,
    "clean_voice_end": False,
    "clean_voice_schedule": False,
    "clean_voice_invite": False,
    "clean_pinned": False,

    # Custom Block
    "custom_block_list": [], # list of strings or regex
    
    # Message Length Section
    "msg_length_min": 0,
    "msg_length_max": 2000,
    "msg_length_penalty": "off", # off, warn, kick, mute, ban
    "msg_length_delete": False,
    
    # User Permissions (Free system)
    "user_permissions": {}, # {user_id: {"block_stickers": True, ...}} where True means they ARE allowed (freed)

    # Group Regulations
    "group_rules": "No rules set yet.",
    
    # Command Permissions
    # 0: nobody (✖️), 1: staff (👮), 2: everyone (👥), 3: private (🤖)
    "cmd_perms": {
        "staff": 2,
        "rules": 1,
        "me": 3,
        "translate": 2,
        "link": 2
    },
    
    # Filters
    "filters": {}, # {trigger: {"text": "...", "file_id": "...", "type": "..."}}

    # Report System (@admin)
    "report_settings": {
        "status": True,
        "send_to": "founder", # nobody, founder, staff_group
        "tag_founder": False,
        "tag_admins": False,
        "only_in_reply": False,
        "reason_required": False,
        "delete_if_resolved": False
    },

    # Message Self-Destruction
    "self_destruct_time": 0, # Time in seconds, 0 means off

    # Anti-Spam (Updated)
    "antispam_tg_links": False,
    "antispam_tg_links_penalty": "off",
    "antispam_tg_links_delete": False,
    "antispam_username": False,
    "antispam_bots": False,
    "antispam_forwarding": False,
    "antispam_forward_channels_penalty": "off",
    "antispam_forward_groups_penalty": "off",
    "antispam_forward_users_penalty": "off",
    "antispam_forward_bots_penalty": "off",
    "antispam_quote": False,
    "antispam_quote_channels_penalty": "off",
    "antispam_quote_groups_penalty": "off",
    "antispam_quote_users_penalty": "off",
    "antispam_quote_bots_penalty": "off",
    "antispam_total_links": False,
    "antispam_total_links_penalty": "off",
    "antispam_total_links_delete": False,
    "antispam_whitelist": [], # Whitelisted links/usernames

    # Antiflood (Updated)
    "antiflood_messages": 5,
    "antiflood_time": 3,
    "antiflood_punishment": "off",
    "antiflood_delete": False,

    # Group Link (New)
    "custom_group_link": None,

    # Permissions (New)
    "anon_admin_enabled": False,
    "anon_admin_perms": {
        "ban": False,
        "pin": False,
        "delete": False,
        "add_admin": False
    },
    "change_settings_mode": "info", # "all" or "info"
    "custom_roles_enabled": False,

    # Members Management (New)
    "members_mgmt_kick_muted": False,
    "members_mgmt_kick_deleted": False
}

def get_default_settings():
    return copy.deepcopy(DEFAULT_SETTINGS)

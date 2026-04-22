import logging
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGODB_URI, DEFAULT_SETTINGS, group_settings
import copy

# Database setup
client = AsyncIOMotorClient(MONGODB_URI)
db = client['grouphelp_db']
settings_collection = db['settings']
users_collection = db['users']  # New collection for username->ID mapping

# In-memory cache for quick username lookups
users_db = {}

async def load_all_settings():
    """Loads all settings from MongoDB into the in-memory cache."""
    global group_settings
    try:
        async for doc in settings_collection.find():
            chat_id = doc.get('chat_id')
            if chat_id:
                # Remove _id and chat_id before caching
                data = {k: v for k, v in doc.items() if k not in ['_id', 'chat_id']}
                group_settings[chat_id] = data
        logging.info(f"Loaded {len(group_settings)} chat settings from MongoDB.")
    except Exception as e:
        logging.error(f"Error loading settings from MongoDB: {e}")

def convert_keys_to_strings(data):
    """Recursively convert all dictionary keys to strings for MongoDB compatibility."""
    if isinstance(data, dict):
        return {str(k): convert_keys_to_strings(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_keys_to_strings(item) for item in data]
    else:
        return data

async def save_settings(chat_id: int):
    """Saves a specific chat's settings to MongoDB."""
    if chat_id not in group_settings:
        return
        
    try:
        data = copy.deepcopy(group_settings[chat_id])
        # Convert all keys to strings for MongoDB
        data = convert_keys_to_strings(data)
        await settings_collection.update_one(
            {'chat_id': chat_id},
            {'$set': data},
            upsert=True
        )
    except Exception as e:
        logging.error(f"Error saving settings for {chat_id} to MongoDB: {e}")

async def get_chat_settings(chat_id: int):
    """Gets settings for a chat, loading from DB if not in cache."""
    if chat_id in group_settings:
        return group_settings[chat_id]
        
    try:
        doc = await settings_collection.find_one({'chat_id': chat_id})
        if doc:
            data = {k: v for k, v in doc.items() if k not in ['_id', 'chat_id']}
            group_settings[chat_id] = data
            return data
    except Exception as e:
        logging.error(f"Error fetching settings for {chat_id}: {e}")
        
    # If not in DB, initialize with defaults
    group_settings[chat_id] = copy.deepcopy(DEFAULT_SETTINGS)
    await save_settings(chat_id)
    return group_settings[chat_id]

async def update_setting(chat_id: int, key: str, value):
    """Updates a single setting and saves to DB."""
    if chat_id not in group_settings:
        await get_chat_settings(chat_id)
        
    group_settings[chat_id][key] = value
    await save_settings(chat_id)

async def load_users_db():
    """Loads all username->ID mappings from MongoDB into the in-memory cache."""
    global users_db
    try:
        async for doc in users_collection.find():
            username = doc.get('username')
            user_id = doc.get('user_id')
            if username and user_id:
                users_db[username.lower()] = user_id
        logging.info(f"Loaded {len(users_db)} users into username database.")
    except Exception as e:
        logging.error(f"Error loading users database: {e}")

async def save_user(username: str, user_id: int):
    """Saves or updates a username->ID mapping in the database."""
    if not username:
        return
    
    username_lower = username.lower()
    try:
        # Update in-memory cache
        users_db[username_lower] = user_id
        
        # Update in MongoDB
        await users_collection.update_one(
            {'username': username_lower},
            {'$set': {'username': username_lower, 'user_id': user_id}},
            upsert=True
        )
        logging.info(f"Saved user: @{username} -> {user_id}")
    except Exception as e:
        logging.error(f"Error saving user {username}: {e}")

async def get_user_id_by_username(username: str) -> int:
    """Gets user ID by username from the database."""
    if not username:
        return None
    
    username_lower = username.lower()
    
    # Check in-memory cache first
    if username_lower in users_db:
        return users_db[username_lower]
    
    # Check MongoDB
    try:
        doc = await users_collection.find_one({'username': username_lower})
        if doc:
            user_id = doc.get('user_id')
            # Cache it for future lookups
            users_db[username_lower] = user_id
            return user_id
    except Exception as e:
        logging.error(f"Error fetching user {username}: {e}")
    
    return None

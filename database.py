import logging
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGODB_URI, DEFAULT_SETTINGS, group_settings
import copy

# Database setup
client = AsyncIOMotorClient(MONGODB_URI)
db = client['grouphelp_db']
settings_collection = db['settings']

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

async def save_settings(chat_id: int):
    """Saves a specific chat's settings to MongoDB."""
    if chat_id not in group_settings:
        return
        
    try:
        data = copy.deepcopy(group_settings[chat_id])
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

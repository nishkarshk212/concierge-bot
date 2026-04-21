
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://lilyy67u_db_user:Nishkarsh123@grouphelp2.06f2yus.mongodb.net/?appName=Grouphelp2")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8409128631:AAHOn4mYiptXjFuXhHeXguF5NbgLkJKCvWM")

async def check_settings():
    from telegram import Bot
    bot = Bot(token=BOT_TOKEN)
    
    chat_id = -1003333223527
    
    # Check bot permissions
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(chat_id, me.id)
        print(f"Bot status in {chat_id}: {member.status}")
        if hasattr(member, 'can_send_messages'):
            print(f"  Can send messages: {member.can_send_messages}")
        if hasattr(member, 'can_invite_users'):
            print(f"  Can invite users (required for CHAT_MEMBER updates): {member.can_invite_users}")
    except Exception as e:
        print(f"Error checking bot status: {e}")

    client = AsyncIOMotorClient(MONGODB_URI)
    db = client['grouphelp_db']
    settings_collection = db['settings']
    
    chat_id = -1003333223527
    doc = await settings_collection.find_one({'chat_id': chat_id})
    if doc:
        print(f"Settings for {chat_id}:")
        for k, v in doc.items():
            if k != 'seen_users': # Don't print potentially thousands of IDs
                print(f"  {k}: {v}")
            else:
                print(f"  seen_users: {len(v)} users")
    else:
        print(f"No settings found for {chat_id}")

if __name__ == "__main__":
    asyncio.run(check_settings())

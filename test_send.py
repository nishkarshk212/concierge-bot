
import asyncio
from telegram import Bot
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8409128631:AAHOn4mYiptXjFuXhHeXguF5NbgLkJKCvWM")

async def send_test():
    bot = Bot(token=BOT_TOKEN)
    chat_id = -1003333223527
    try:
        msg = await bot.send_message(chat_id=chat_id, text="🔄 Bot is restarting and checking welcome message settings...")
        print(f"Message sent! ID: {msg.message_id}")
    except Exception as e:
        print(f"Error sending message: {e}")

if __name__ == "__main__":
    asyncio.run(send_test())

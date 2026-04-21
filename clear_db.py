import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# MongoDB URI from config or env
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://lilyy67u_db_user:Nishkarsh123@grouphelp2.06f2yus.mongodb.net/?appName=Grouphelp2")

async def clear_database():
    """Clears all data from the grouphelp_db database."""
    try:
        logger.info("Connecting to MongoDB...")
        client = AsyncIOMotorClient(MONGODB_URI)
        db = client['grouphelp_db']
        
        # List collections
        collections = await db.list_collection_names()
        logger.info(f"Found collections: {collections}")
        
        for coll_name in collections:
            logger.info(f"Clearing collection: {coll_name}")
            await db[coll_name].delete_many({})
            logger.info(f"Successfully cleared {coll_name}")
            
        logger.info("Database cleared successfully.")
        client.close()
    except Exception as e:
        logger.error(f"Error clearing database: {e}")

if __name__ == "__main__":
    asyncio.run(clear_database())

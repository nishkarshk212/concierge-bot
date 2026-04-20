"""
Script to clear all settings from MongoDB database
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGODB_URI

async def clear_database():
    """Clear all settings from the database"""
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client['grouphelp_db']
    settings_collection = db['settings']
    
    # Count documents before deletion
    count = await settings_collection.count_documents({})
    print(f"Found {count} documents in database")
    
    # Delete all documents
    result = await settings_collection.delete_many({})
    print(f"Deleted {result.deleted_count} documents")
    
    # Verify deletion
    count_after = await settings_collection.count_documents({})
    print(f"Documents remaining: {count_after}")
    
    client.close()
    print("Database cleared successfully!")

if __name__ == "__main__":
    asyncio.run(clear_database())

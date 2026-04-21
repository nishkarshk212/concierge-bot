"""
Script to clear all settings from MongoDB database and start fresh
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGODB_URI

async def clear_database():
    """Clear all settings from the database"""
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client['grouphelp_db']
    settings_collection = db['settings']
    
    print("=" * 60)
    print("🗑️  DATABASE CLEAR UTILITY")
    print("=" * 60)
    
    # Count documents before deletion
    count = await settings_collection.count_documents({})
    print(f"\n📊 Found {count} documents in database")
    
    if count == 0:
        print("✅ Database is already empty!")
        client.close()
        return
    
    # Show collections info
    collections = await db.list_collection_names()
    print(f"\n📁 Collections: {', '.join(collections)}")
    
    # Delete all documents
    print(f"\n⚠️  Deleting all {count} documents...")
    result = await settings_collection.delete_many({})
    print(f"✅ Deleted {result.deleted_count} documents")
    
    # Verify deletion
    count_after = await settings_collection.count_documents({})
    print(f"📊 Documents remaining: {count_after}")
    
    if count_after == 0:
        print("\n" + "=" * 60)
        print("✅ DATABASE CLEARED SUCCESSFULLY!")
        print("=" * 60)
        print("\n🚀 Bot will start fresh with default settings")
        print("📝 All groups will be initialized with fresh configuration")
    else:
        print(f"\n⚠️  Warning: {count_after} documents still remain!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(clear_database())


import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import logging

MONGODB_URI = "mongodb+srv://lilyy67u_db_user:Nishkarsh123@grouphelp2.06f2yus.mongodb.net/?appName=Grouphelp2&retryWrites=true&w=majority&tls=true"

async def check_db():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client['grouphelp_db']
    collection = db['settings']
    
    print(f"Checking collection: {collection.name}")
    
    # List all chat_ids and count occurrences
    pipeline = [
        {"$group": {"_id": "$chat_id", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gt": 1}}}
    ]
    
    duplicates = await collection.aggregate(pipeline).to_list(length=None)
    
    if duplicates:
        print(f"Found {len(duplicates)} duplicate chat_ids:")
        for dup in duplicates:
            print(f"Chat ID: {dup['_id']}, Count: {dup['count']}")
    else:
        print("No duplicate chat_ids found in database.")
    
    total = await collection.count_documents({})
    print(f"Total documents in settings: {total}")
    
    # Check for any suspicious entries
    sample = await collection.find_one()
    if sample:
        print(f"Sample document keys: {list(sample.keys())}")

if __name__ == "__main__":
    asyncio.run(check_db())

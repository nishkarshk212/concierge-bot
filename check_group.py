import asyncio
import httpx

async def check_group_info():
    bot_token = "8409128631:AAHOn4mYiptXjFuXhHeXguF5NbgLkJKCvWM"
    chat_id = -1003333223527
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.telegram.org/bot{bot_token}/getChat",
            json={"chat_id": chat_id}
        )
        data = response.json()
        
        if data.get("ok"):
            chat = data["result"]
            title = chat.get("title")
            chat_type = chat.get("type")
            has_forum = chat.get("is_forum", False)
            
            print(f"Group: {title}")
            print(f"Type: {chat_type}")
            print(f"Has forum/topics: {has_forum}")
            
            if has_forum:
                print("\n⚠️ GROUP HAS TOPICS ENABLED!")
                print("This can interfere with chat_member updates.")
        else:
            print(f"Error: {data}")

asyncio.run(check_group_info())

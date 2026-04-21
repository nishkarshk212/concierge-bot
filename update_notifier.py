"""
Update Notifier - Sends update notifications to log group when bot is updated
"""
import logging
from datetime import datetime
from config import LOG_GROUP_ID

async def send_update_notification(bot, features_added, service_name="titanic-bot"):
    """
    Send update notification to log group
    
    Args:
        bot: Telegram bot instance
        features_added: List of features/changes added in this update
        service_name: Name of the bot service on server (default: titanic-bot)
    """
    try:
        bot_info = await bot.get_me()
        
        # Build the update notification message
        update_text = (
            f"🔄 <b>BOT UPDATE DEPLOYED</b>\n\n"
            f"❅─────✧❅✦❅✧─────❅\n\n"
            f"🤖 <b>BOT:</b> {bot_info.mention_html()}\n"
            f"🖥️ <b>SERVICE:</b> {service_name}\n"
            f"📅 <b>DATE:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
            f"📦 <b>UPDATE DETAILS:</b>\n"
        )
        
        # Add each feature as a bullet point
        for i, feature in enumerate(features_added, 1):
            update_text += f"  {i}. {feature}\n"
        
        update_text += (
            f"\n✅ <b>STATUS:</b> Successfully deployed and running!\n"
            f"🚀 <b>All systems operational!</b>"
        )
        
        # Send to log group
        await bot.send_message(LOG_GROUP_ID, update_text, parse_mode='HTML')
        logging.info(f"Update notification sent to log group: {len(features_added)} features listed")
        
    except Exception as e:
        logging.error(f"Failed to send update notification: {e}")


async def send_startup_with_updates(bot, features_added=None, service_name="titanic-bot"):
    """
    Send startup message with optional update details
    
    Args:
        bot: Telegram bot instance
        features_added: Optional list of new features (if this is an update)
        service_name: Name of the bot service on server
    """
    bot_info = await bot.get_me()
    
    if features_added:
        # This is an update - send detailed update notification
        await send_update_notification(bot, features_added, service_name)
    else:
        # Regular startup - send basic startup message
        startup_text = (
            f"🚀 <b>BOT STARTED SUCCESSFULLY</b>\n\n"
            f"❅─────✧❅✦❅✧─────❅\n\n"
            f"🤖 <b>BOT:</b> {bot_info.mention_html()}\n"
            f"🖥️ <b>SERVICE:</b> {service_name}\n"
            f"🗑️ <b>DATABASE:</b> Fresh & Clean\n"
            f"🛡️ <b>STATUS:</b> Active & Running\n"
            f"📅 <b>DATE:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
            f"✅ <b>READY:</b> All systems operational!"
        )
        try:
            await bot.send_message(LOG_GROUP_ID, startup_text, parse_mode='HTML')
        except Exception as e:
            logging.error(f"Error sending startup log: {e}")

import logging
from telegram import Update, Message
from telegram.ext import ContextTypes

async def delete_msg_job(context: ContextTypes.DEFAULT_TYPE):
    """Job to delete a message."""
    job = context.job
    try:
        logging.info(f"SELF-DESTRUCT: Deleting message {job.data} in chat {job.chat_id}")
        await context.bot.delete_message(chat_id=job.chat_id, message_id=job.data)
        logging.info(f"SELF-DESTRUCT: Successfully deleted message {job.data}")
    except Exception as e:
        logging.error(f"SELF-DESTRUCT: Failed to delete message {job.data} in chat {job.chat_id}: {e}")

async def schedule_self_destruction(update: Update, context: ContextTypes.DEFAULT_TYPE, settings: dict):
    """Schedules self-destruction for a message if enabled."""
    if not update or not update.effective_message:
        return

    # Check if self-destruction is enabled
    sd_time = settings.get("self_destruct_time", 0)
    bot_sd_enabled = settings.get("bot_self_destruct", False)
    
    # If self-destruction is disabled completely, skip
    if sd_time == 0:
        return
    
    message = update.effective_message
    is_bot_message = message.from_user and message.from_user.id == context.bot.id
    
    # Check if we should delete this specific message
    # If it's a bot message, check bot_self_destruct setting
    # If it's a user message, it's always deleted if sd_time > 0
    if is_bot_message and not bot_sd_enabled:
        return

    chat_id = update.effective_chat.id
    message_id = message.message_id
    
    try:
        # Schedule deletion
        logging.info(f"SELF-DESTRUCT: Scheduling deletion for message {message_id} in {sd_time} seconds (chat: {chat_id})")
        context.job_queue.run_once(
            delete_msg_job, 
            sd_time, 
            chat_id=chat_id, 
            data=message_id,
            name=f"sd_{chat_id}_{message_id}"
        )
        logging.info(f"SELF-DESTRUCT: Job scheduled successfully for message {message_id}")
    except Exception as e:
        logging.error(f"SELF-DESTRUCT: Failed to schedule deletion for message {message_id}: {e}")

async def schedule_bot_message_destruction(message: Message, context: ContextTypes.DEFAULT_TYPE, settings: dict):
    """Schedules self-destruction for a message sent by the bot."""
    if not message:
        return

    sd_time = settings.get("self_destruct_time", 0)
    bot_sd_enabled = settings.get("bot_self_destruct", False)
    
    if sd_time > 0 and bot_sd_enabled:
        chat_id = message.chat_id
        message_id = message.message_id
        
        try:
            logging.info(f"SELF-DESTRUCT: Scheduling bot message deletion for {message_id} in {sd_time}s")
            context.job_queue.run_once(
                delete_msg_job, 
                sd_time, 
                chat_id=chat_id, 
                data=message_id,
                name=f"sd_bot_{chat_id}_{message_id}"
            )
        except Exception as e:
            logging.error(f"SELF-DESTRUCT: Failed to schedule bot message deletion: {e}")

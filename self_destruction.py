import logging
from telegram import Update
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
    if not update.effective_message:
        return

    # Check if self-destruction is enabled
    sd_time = settings.get("self_destruct_time", 0)
    
    if sd_time == 0:
        # Self-destruction is disabled, skip
        return
    
    if sd_time > 0:
        chat_id = update.effective_chat.id
        message_id = update.effective_message.message_id
        
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

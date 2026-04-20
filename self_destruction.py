import logging
from telegram import Update
from telegram.ext import ContextTypes

async def delete_msg_job(context: ContextTypes.DEFAULT_TYPE):
    """Job to delete a message."""
    job = context.job
    try:
        await context.bot.delete_message(chat_id=job.chat_id, message_id=job.data)
    except Exception as e:
        logging.error(f"Error in delete_msg_job: {e}")

async def schedule_self_destruction(update: Update, context: ContextTypes.DEFAULT_TYPE, settings: dict):
    """Schedules self-destruction for a message if enabled."""
    if not update.effective_message:
        return

    # Check if self-destruction is enabled
    sd_time = settings.get("self_destruct_time", 0)
    if sd_time > 0:
        chat_id = update.effective_chat.id
        message_id = update.effective_message.message_id
        
        # Schedule deletion
        context.job_queue.run_once(
            delete_msg_job, 
            sd_time, 
            chat_id=chat_id, 
            data=message_id,
            name=f"sd_{chat_id}_{message_id}"
        )

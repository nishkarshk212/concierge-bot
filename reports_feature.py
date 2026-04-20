from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import group_settings, DEFAULT_SETTINGS
from database import get_chat_settings
from font import apply_font
from common import apply_font

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles @admin and /report commands."""
    if not update.message:
        return

    chat_id = update.effective_chat.id
    settings = await get_chat_settings(chat_id)
    report_settings = settings.get("report_settings", DEFAULT_SETTINGS["report_settings"])
    
    if not report_settings.get("status"):
        return

    # Check if user is admin/mod (they can't use report)
    user_id = update.effective_user.id
    try:
        member = await update.effective_chat.get_member(user_id)
        if member.status in ["administrator", "creator"]:
            return
    except Exception:
        pass

    # Only in reply check
    if report_settings.get("only_in_reply") and not update.message.reply_to_message:
        await update.message.reply_text(apply_font("This command can only be used in reply to a message."))
        return

    # Reason required check
    reason = " ".join(context.args) if context.args else ""
    if report_settings.get("reason_required") and not reason:
        await update.message.reply_text(apply_font("You must provide a reason for the report."))
        return

    send_to = report_settings.get("send_to", "founder")
    if send_to == "nobody":
        return

    # Prepare report message
    reporter = update.effective_user.mention_html()
    reported_msg = update.message.reply_to_message
    
    report_text = f"🆘 <b>New Report</b>\n\n"
    report_text += f"👤 <b>Reporter:</b> {reporter}\n"
    if reason:
        report_text += f"📝 <b>Reason:</b> {reason}\n"
    
    if reported_msg:
        reported_user = reported_msg.from_user.mention_html()
        report_text += f"👤 <b>Reported user:</b> {reported_user}\n"
        report_text += f"🔗 <b>Message:</b> <a href='{reported_msg.link}'>Link</a>\n"

    # Add tags
    tags = ""
    if report_settings.get("tag_founder"):
        # We need to find the founder
        try:
            admins = await update.effective_chat.get_administrators()
            for admin in admins:
                if admin.status == "creator":
                    tags += f"{admin.user.mention_html()} "
                    break
        except Exception:
            pass
    
    if report_settings.get("tag_admins"):
        tags += "@admin "

    if tags:
        report_text += f"\n{tags}"

    # Send to destination
    reply_markup = None
    if report_settings.get("delete_if_resolved"):
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Resolved ✅", callback_data=f"resolve_report_{reported_msg.message_id if reported_msg else 0}")]])

    if send_to == "founder":
        await update.message.reply_text(report_text, parse_mode='HTML', reply_markup=reply_markup)
    elif send_to == "staff_group":
        staff_group_id = settings.get("staff_group_id")
        if staff_group_id:
            await context.bot.send_message(staff_group_id, report_text, parse_mode='HTML', reply_markup=reply_markup)
        else:
            await update.message.reply_text(report_text + "\n\n<i>(Staff group not configured)</i>", parse_mode='HTML', reply_markup=reply_markup)

async def handle_reports_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks if a message contains @admin and triggers the report logic."""
    if update.message and update.message.text and "@admin" in update.message.text.lower():
        await report_command(update, context)
        return True
    return False

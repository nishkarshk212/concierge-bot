from telegram import Update, MessageEntity
from config import group_settings, DEFAULT_SETTINGS

async def handle_blocking(update: Update, context):
    """Handles all blocking logic for messages."""
    if not update.effective_chat or update.effective_chat.type == "private":
        return False

    chat_id = update.effective_chat.id
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    msg = update.effective_message
    if not msg:
        return False

    should_delete = False
    penalty_reason = ""
    
    # Check Message Length
    if msg.text or msg.caption:
        content = (msg.text or "") + (msg.caption or "")
        length = len(content)
        min_l = settings.get("msg_length_min", 0)
        max_l = settings.get("msg_length_max", 2000)
        penalty = settings.get("msg_length_penalty", "off")
        
        if length < min_l or length > max_l:
            if penalty != "off":
                # Check if user is admin
                member = await context.bot.get_chat_member(chat_id, update.effective_user.id)
                if member.status not in ["administrator", "creator"]:
                    penalty_reason = f"Message length {length} is outside allowed range ({min_l}-{max_l})!"
                    
                    if settings.get("msg_length_delete"):
                        should_delete = True
                    
                    # Apply penalty
                    user_id = update.effective_user.id
                    try:
                        if penalty == "warn":
                            await msg.reply_text(f"⚠️ {penalty_reason}")
                        elif penalty == "kick":
                            await context.bot.ban_chat_member(chat_id, user_id)
                            await context.bot.unban_chat_member(chat_id, user_id)
                            await msg.reply_text(f"👞 {penalty_reason} User kicked.")
                        elif penalty == "mute":
                            from datetime import datetime, timedelta
                            await context.bot.restrict_chat_member(chat_id, user_id, permissions={"can_send_messages": False}, until_date=datetime.now() + timedelta(hours=1))
                            await msg.reply_text(f"🔇 {penalty_reason} User muted for 1 hour.")
                        elif penalty == "ban":
                            await context.bot.ban_chat_member(chat_id, user_id)
                            await msg.reply_text(f"🚫 {penalty_reason} User banned.")
                    except Exception as e:
                        import logging
                        logging.error(f"Penalty error: {e}")

    # Check if user is freed from specific blocking
    if not update.effective_user:
        return False
        
    user_id = update.effective_user.id
    user_perms = settings.get("user_permissions", {}).get(user_id, {})

    # Helper to check if user is freed from a specific block
    def is_user_freed(block_key):
        return user_perms.get(block_key, False)

    # Check for basic types
    if msg.sticker:
        # Check if it's a premium sticker or a custom emoji sticker
        is_premium = bool(msg.sticker.premium_animation or msg.sticker.custom_emoji_id)
        
        if settings.get("block_stickers") and not is_user_freed("block_stickers"):
            should_delete = True
        elif is_premium and settings.get("block_premium_sticker") and not is_user_freed("block_premium_sticker"):
            should_delete = True
    
    # Check for custom emojis and links in entities
    entities = list(msg.entities or []) + list(msg.caption_entities or [])
    for entity in entities:
        if entity.type == MessageEntity.CUSTOM_EMOJI:
            if settings.get("block_premium_sticker") and not is_user_freed("block_premium_sticker"):
                should_delete = True
        elif entity.type == MessageEntity.URL:
            if settings.get("block_link") and not is_user_freed("block_link"):
                should_delete = True
        elif entity.type == MessageEntity.TEXT_LINK:
            if settings.get("block_embed_link") and not is_user_freed("block_embed_link"):
                should_delete = True

    if msg.photo or msg.video or msg.animation:
        if settings.get("block_media") and not is_user_freed("block_media"):
            should_delete = True
            
    if msg.document:
        if settings.get("block_documents") and not is_user_freed("block_documents"):
            should_delete = True
            
    # Check for forwarded messages
    # Note: PTB v20.x uses forward_from, PTB v21+ uses forward_origin
    is_forwarded = (hasattr(msg, 'forward_origin') and msg.forward_origin is not None) or \
                   (hasattr(msg, 'forward_from') and msg.forward_from is not None)
    
    if is_forwarded:
        import logging
        logging.info(f"Forward check: User {update.effective_user.id} sent forwarded message in chat {chat_id}")
        logging.info(f"Forward check: block_forward={settings.get('block_forward')}, is_user_freed={is_user_freed('block_forward')}")
        
        if settings.get("block_forward") and not is_user_freed("block_forward"):
            logging.info(f"Forward blocking: Deleting forwarded message from user {update.effective_user.id} in chat {chat_id}")
            should_delete = True
        elif getattr(msg, 'forward_origin', None) and getattr(msg.forward_origin, 'chat', None) and msg.forward_origin.chat.type == "channel" and settings.get("block_channel_post") and not is_user_freed("block_channel_post"):
            logging.info(f"Channel post blocking: Deleting channel post from user {update.effective_user.id}")
            should_delete = True
        elif getattr(msg, 'forward_from_chat', None) and msg.forward_from_chat.type == "channel" and settings.get("block_channel_post") and not is_user_freed("block_channel_post"):
            logging.info(f"Channel post blocking (old API): Deleting channel post from user {update.effective_user.id}")
            should_delete = True
    else:
        import logging
        logging.debug(f"Message from user {update.effective_user.id} is NOT forwarded")
            
    # Check for commands (block_command)
    if msg.text and msg.text.startswith("/") and settings.get("block_command") and not is_user_freed("block_command"):
        import logging
        # Allow essential bot commands
        allowed_cmds = ("/start", "/settings", "/free", "/help", "/rules", "/me", "/info", "/link", "/report")
        if not any(msg.text.startswith(cmd) for cmd in allowed_cmds):
            logging.info(f"Command blocking: Deleting command {msg.text.split()[0]} from user {update.effective_user.id}")
            should_delete = True
            
    if msg.contact and settings.get("block_contact") and not is_user_freed("block_contact"):
        should_delete = True
        
    if msg.location and settings.get("block_location") and not is_user_freed("block_location"):
        should_delete = True
        
    if msg.voice and settings.get("block_voice") and not is_user_freed("block_voice"):
        should_delete = True

    # Block music/audio files (mp3, m4a, wav, etc.)
    if msg.audio and settings.get("block_audio") and not is_user_freed("block_audio"):
        import logging
        # Get audio file info if available
        audio_info = ""
        if hasattr(msg.audio, 'file_name') and msg.audio.file_name:
            audio_info = f" ({msg.audio.file_name})"
        elif hasattr(msg.audio, 'performer') and msg.audio.performer:
            audio_info = f" by {msg.audio.performer}"
        
        logging.info(f"Music blocking: Deleting audio file from user {update.effective_user.id}{audio_info} in chat {chat_id}")
        should_delete = True
        
    if msg.video_note and settings.get("block_video_note") and not is_user_freed("block_video_note"):
        should_delete = True
        
    if msg.poll and settings.get("block_poll") and not is_user_freed("block_poll"):
        should_delete = True

    if msg.dice and settings.get("block_dice") and not is_user_freed("block_dice"):
        should_delete = True

    if msg.game and settings.get("block_game") and not is_user_freed("block_game"):
        should_delete = True

    # Custom Block List (text or caption)
    content_to_check = (msg.text or "") + (msg.caption or "")
    if content_to_check and settings.get("custom_block_list"):
        for blocked_word in settings["custom_block_list"]:
            if blocked_word.lower() in content_to_check.lower():
                should_delete = True
                break

    if should_delete:
        try:
            # Check if user is admin - usually admins are exempt from blocking
            member = await context.bot.get_chat_member(chat_id, update.effective_user.id)
            if member.status in ["administrator", "creator"]:
                return False
            
            # Send notification for blocked content
            is_forwarded_msg = (hasattr(msg, 'forward_origin') and msg.forward_origin is not None) or \
                              (hasattr(msg, 'forward_from') and msg.forward_from is not None)
            
            if msg.audio and settings.get("block_audio"):
                try:
                    await msg.reply_text(
                        f"🎵 <b>Music files are not allowed in this group.</b>\n\n"
                        f"<i>Your audio file has been automatically deleted.</i>",
                        parse_mode='HTML'
                    )
                except Exception:
                    pass  # Ignore if can't send notification
            elif is_forwarded_msg and settings.get("block_forward"):
                try:
                    await msg.reply_text(
                        f"⚠️ <b>Forwarded messages are not allowed in this group.</b>\n\n"
                        f"<i>Your forwarded message has been automatically deleted.</i>",
                        parse_mode='HTML'
                    )
                except Exception:
                    pass  # Ignore if can't send notification
                
            await msg.delete()
            return True
        except Exception:
            pass
            
    return False

async def handle_clean_service(update: Update, context):
    """Handles cleaning service messages (joins, leaves, etc.). Returns True if message was deleted."""
    if not update.effective_chat or update.effective_chat.type == "private":
        return False

    chat_id = update.effective_chat.id
    settings = group_settings.get(chat_id, DEFAULT_SETTINGS)
    msg = update.effective_message
    if not msg:
        return False

    should_delete = False

    if msg.new_chat_members and settings.get("clean_join"):
        should_delete = True
    elif msg.left_chat_member and settings.get("clean_left"):
        should_delete = True
    elif msg.new_chat_title and settings.get("clean_title"):
        should_delete = True
    elif (msg.new_chat_photo or msg.delete_chat_photo) and settings.get("clean_photo"):
        should_delete = True
    elif (getattr(msg, 'video_chat_started', None) or getattr(msg, 'voice_chat_started', None)) and settings.get("clean_voice_start"):
        should_delete = True
    elif (getattr(msg, 'video_chat_ended', None) or getattr(msg, 'voice_chat_ended', None)) and settings.get("clean_voice_end"):
        should_delete = True
    elif (getattr(msg, 'video_chat_scheduled', None) or getattr(msg, 'voice_chat_scheduled', None)) and settings.get("clean_voice_schedule"):
        should_delete = True
    elif (getattr(msg, 'video_chat_participants_invited', None) or getattr(msg, 'voice_chat_participants_invited', None)) and settings.get("clean_voice_invite"):
        should_delete = True
    elif msg.pinned_message and settings.get("clean_pinned"):
        should_delete = True

    if should_delete:
        try:
            import logging
            logging.info(f"Cleaning service message in chat {chat_id}: {msg.message_id}")
            await msg.delete()
            return True
        except Exception as e:
            import logging
            logging.error(f"Error deleting service message: {e}")
            
    return False
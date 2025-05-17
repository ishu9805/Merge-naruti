from telegram import Update
from telegram.ext import CallbackContext, ChatMemberHandler
from shivu import application  # Assuming LOGGER_ID is the ID for logging
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from shivu import application



from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ChatMemberHandler, CommandHandler
from shivu import application

LOGGER_ID = -1002165460785  # Your log channel ID
AUTHORIZED_USER_IDS = {7378476666}  # Your user ID
BOT_INVITE_LINK = "https://t.me/Fancy_Waifu_Husbando_Bot?startgroup=true"
WELCOME_IMAGE_URL = "https://files.catbox.moe/c93u0p.jpg"  # Your image URL

async def log_chat_member(update: Update, context: CallbackContext) -> None:
    """Handler for when bot is added/removed from groups"""
    if not update.my_chat_member:
        return

    chat = update.effective_chat
    my_chat_member = update.my_chat_member
    from_user = my_chat_member.from_user
    bot = context.bot

    try:
        member_count = await bot.get_chat_members_count(chat.id)
        by_user = (f"{from_user.first_name} (@{from_user.username})" 
                  if from_user and from_user.username 
                  else from_user.first_name if from_user else "Unknown User")

        # Bot added to group
        if my_chat_member.new_chat_member.status in ["member", "administrator"]:
            try:
                invite_link = await bot.export_chat_invite_link(chat.id)
            except Exception:
                invite_link = "No invite link (missing admin rights)"

            # Create inline button
            keyboard = [
                [InlineKeyboardButton("Aᴅᴅ Mᴇ Tᴏ Yᴏᴜʀ Gʀᴏᴜᴘ", url=BOT_INVITE_LINK)]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Welcome message to send to the group
            welcome_text = (
                f"✨ Hello everyone!\n"
                f"🤖 I'm {bot.first_name}, a fancy anime bot!\n"
                f"👤 Added by: {by_user}\n"
                f"👥 Group Members: {member_count}\n\n"
                #f"Use /help to see what I can do!"
            )

            # Log message to send to logger channel
            log_msg = (
                f"➕ **Bot Added to Group**\n\n"
                f"📌 Name: {chat.title}\n"
                f"🆔 ID: `{chat.id}`\n"
                f"👤 By: {by_user}\n"
                f"👥 Members: {member_count}\n"
                f"🔗 Group Link: {invite_link}"
            )

            try:
                # Send photo with caption and button
                await bot.send_photo(
                    chat_id=chat.id,
                    photo=WELCOME_IMAGE_URL,
                    caption=welcome_text,
                    reply_markup=reply_markup
                )
            except Exception as e:
                log_msg += f"\n\n⚠️ Failed to send welcome message: {str(e)[:100]}"
                # Fallback to text message if photo fails
                try:
                    await bot.send_message(
                        chat.id,
                        welcome_text,
                        reply_markup=reply_markup
                    )
                except Exception as e2:
                    log_msg += f"\nAlso failed text fallback: {str(e2)[:100]}"

            await bot.send_message(LOGGER_ID, log_msg, parse_mode="Markdown")

        # Bot removed from group
        elif my_chat_member.new_chat_member.status == "left":
            log_msg = (
                f"➖ **Bot Removed from Group**\n\n"
                f"📌 Name: {chat.title}\n"
                f"🆔 ID: `{chat.id}`\n"
                f"👤 By: {by_user}\n"
                f"👥 Members: {member_count}\n"
                f"🕒 At: {my_chat_member.date}"
            )
            await bot.send_message(LOGGER_ID, log_msg, parse_mode="Markdown")

    except Exception as e:
        error_msg = (
            f"⚠️ Error in chat member update:\n"
            f"Chat: {chat.title if chat else 'Unknown'} ({chat.id if chat else 'N/A'})\n"
            f"Error: {str(e)[:300]}"
        )
        await bot.send_message(LOGGER_ID, error_msg)

# Add handler
application.add_handler(ChatMemberHandler(log_chat_member, block=False))

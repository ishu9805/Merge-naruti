from telegram import Update
from telegram.ext import CallbackContext, ChatMemberHandler
from shivu import application, LOGGER_ID  # Assuming LOGGER_ID is the ID for logging

async def log_chat_member(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    my_chat_member = update.my_chat_member

    # Extracting the user who added/removed the bot
    from_user = my_chat_member.from_user
    by_user = f"{from_user.first_name} (@{from_user.username or 'No Username'})" if from_user else "Unknown User"

    # Get the total number of members in the group
    member_count = await context.bot.get_chat_members_count(chat.id)

    # Try to get the group invite link (requires bot admin privileges)
    invite_link = None
    if my_chat_member.new_chat_member.status in ["member", "administrator"]:
        try:
            invite_link = await context.bot.export_chat_invite_link(chat.id)
        except Exception:
            invite_link = "Unable to generate invite link (insufficient permissions)."

    # If bot is added
    if my_chat_member.new_chat_member.status in ["member", "administrator"]:
        message = (
            f"➕ **Bot Added to a Group**\n\n"
            f"📌 __Group Name:__ {chat.title}\n"
            f"🆔 __Group ID:__ `{chat.id}`\n"
            f"👤 __Added By:__ {by_user}\n"
            f"👥 __Total Members:__ {member_count}\n"
            f"🔗 __Group Link:__ {invite_link or 'N/A'}"
        )

        # Auto leave if total members are less than 40
        if member_count < 40:
            await context.bot.send_message(
                chat_id=chat.id,
                text="🚨 This group does not meet the minimum requirement of 40 members. The bot will now leave.",
            )
            await context.bot.leave_chat(chat_id=chat.id)

            # Log the auto-leave action
            message += f"\n\n🚪 *Action Taken:* Left the group due to insufficient members."
    
    # If bot is removed
    elif my_chat_member.new_chat_member.status == "left":
        message = (
            f"➖ **Bot Removed from a Group**\n\n"
            f"📌 __Group Name:__ {chat.title}\n"
            f"🆔 __Group ID:__ `{chat.id}`\n"
            f"👤 __Removed By:__ {by_user}"
        )
    else:
        # No relevant status change
        return

    # Send the log message to the logger ID
    await context.bot.send_message(chat_id=LOGGER_ID, text=message, parse_mode='Markdown')

# Adding the ChatMemberHandler to handle these events
chat_member_handler = ChatMemberHandler(log_chat_member, block=False)
application.add_handler(chat_member_handler)

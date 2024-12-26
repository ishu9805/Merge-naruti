from telegram import Update
from telegram.ext import CallbackContext, ChatMemberHandler
from shivu import application  # Assuming LOGGER_ID is the ID for logging
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from shivu import application
LOGGER_ID = -1002198664660 # Assuming LOGGER_ID is the ID for logging

async def leave_all(update: Update, context: CallbackContext) -> None:
    # Ensure the command is used by an authorized user (optional)
    authorized_user_id = 7378476666  # Replace with your user ID
    if update.effective_user.id != authorized_user_id:
        await update.effective_message.reply_text("🚫 You are not authorized to use this command.")
        return

    bot = context.bot
    left_groups = []
    total_groups = 0

    # Fetch all chats the bot is a member of
    async for dialog in bot.get_dialogs():
        chat = dialog.chat
        if chat.type in ["group", "supergroup"]:
            total_groups += 1
            try:
                # Get the member count
                member_count = await bot.get_chat_members_count(chat.id)

                # Leave the group if members are fewer than 50
                if member_count < 50:
                    await bot.leave_chat(chat.id)
                    left_groups.append((chat.title, chat.id, member_count))
            except Exception as e:
                # Log any errors (optional)
                await bot.send_message(LOGGER_ID, f"Error while processing chat {chat.title} ({chat.id}): {e}")

    # Send a summary to the user
    if left_groups:
        summary = (
            f"🚪 **Left Groups with Less than 50 Members**\n\n"
            f"💬 *Total Groups Processed:* {total_groups}\n"
            f"📤 *Groups Left:* {len(left_groups)}\n\n"
        )
        for idx, (title, group_id, count) in enumerate(left_groups, start=1):
            summary += f"{idx}. *{title}* (ID: `{group_id}`) - {count} members\n"
    else:
        summary = "✅ The bot is not part of any groups with fewer than 50 members."

    await update.effective_message.reply_text(summary, parse_mode="Markdown")

# Add the handler to the bot
leave_all_handler = CommandHandler("leaveall", leave_all, block=False)
application.add_handler(leave_all_handler)


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

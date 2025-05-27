from telegram import Update
from telegram.ext import CallbackContext, CommandHandler 

from shivu import UPDATE_CHAT, SUPPORT_CHAT, CHARA_CHANNEL_ID, required_group_id, PHOTO_URL, OWNER_ID, PARTNER
from shivu import (
    collectionps as collection,
    top_global_groups_collectionps as top_global_groups_collection,
    group_user_totals_collectionps as group_user_totals_collection,
    user_collectionps as user_collection,
    user_totals_collectionps as user_totals_collection,
    shivuups as shivuu,
    shivuups as app,
    applicationps as application,
    SUPPORT_CHATps as SUPPORT,
    UPDATE_CHATps as UPDATE_CHAT,
    dbps as db,
    pmusersps as pmusers,
    ban_collectionps as ban_collection,
    user_countps as user_count, 
    chat_dataps as chat_data,
)
async def gbroadcast(update: Update, context: CallbackContext) -> None:
    
    if update.effective_user.id != 7378476666:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    message_to_broadcast = update.message.reply_to_message

    if message_to_broadcast is None:
        await update.message.reply_text("Please reply to a message to broadcast.")
        return

    all_chats = await top_global_groups_collection.distinct("group_id")
    #  all_users = await pm_users.distinct("_id")

    shuyaa = list(set(all_chats))

    failed_sends = 0

    for chat_id in shuyaa:
        try:
            await context.bot.forward_message(chat_id=chat_id,
                                              from_chat_id=message_to_broadcast.chat_id,
                                              message_id=message_to_broadcast.message_id)
        except Exception as e:
            print(f"Failed to send message to {chat_id}: {e}")
            failed_sends += 1

    await update.message.reply_text(f"Broadcast complete. Failed to send to {failed_sends} chats/users.")

application.add_handler(CommandHandler("ggbroadcast", gbroadcast, block=False))


async def ubroadcast(update: Update, context: CallbackContext) -> None:
    
    if update.effective_user.id != 7378476666:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    message_to_broadcast = update.message.reply_to_message

    if message_to_broadcast is None:
        await update.message.reply_text("Please reply to a message to broadcast.")
        return

    all_chats = await user_collection.distinct("id")
    #  all_users = await pm_users.distinct("_id")

    shuyaa = list(set(all_chats))

    failed_sends = 0

    for chat_id in shuyaa:
        try:
            await context.bot.forward_message(chat_id=chat_id,
                                              from_chat_id=message_to_broadcast.chat_id,
                                              message_id=message_to_broadcast.message_id)
        except Exception as e:
            print(f"Failed to send message to {chat_id}: {e}")
            failed_sends += 1

    await update.message.reply_text(f"Broadcast complete. Failed to send to {failed_sends} chats/users.")

application.add_handler(CommandHandler("ugbroadcast", ubroadcast, block=False))

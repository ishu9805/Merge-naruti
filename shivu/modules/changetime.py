from pymongo import ReturnDocument
from pyrogram.enums import ChatMemberStatus
#from shivu import user_totals_collection, shivuu, ban_collection
from pyrogram import Client, filters
from pyrogram.types import Message
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
    UPDATE_CHATps as UPDATE_CHAT_PS,
    dbps as db,
    pmusersps as pmusers,
    ban_collectionps as ban_collection,
    user_countps as user_count, 
    chat_dataps as chat_data,
)
### Constants ###

ADMINS = [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]

### Helper Functions ###

async def get_member_status(chat_id: int, user_id: int) -> ChatMemberStatus:
    member = await shivuu.get_chat_member(chat_id, user_id)
    return member.status

### Main Function ###

@shivuu.on_message(filters.command("changetime"))
async def change_time(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        # If the user is banned, do nothing
        return
    else:
        pass

    # Check if the user is an admin
    if await get_member_status(chat_id, user_id) not in ADMINS:
        await message.reply_text("⚠️ **Admin Access Only!**")
        return

    try:
        args = message.command
        if len(args) != 2:
            await message.reply_text("ℹ️ **Usage:** `/changetime [number]`")
            return

        new_frequency = int(args[1])
        if new_frequency < 70:
            await message.reply_text("⏳ **Frequency must be 70 or higher.**")
            return

        await user_totals_collection.find_one_and_update(
            {'chat_id': str(chat_id)},
            {'$set': {'message_frequency': new_frequency}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        await message.reply_text(f"✅ **Frequency set to {new_frequency}.**")
    except Exception as e:
        await message.reply_text(f"❌ **Error:** {str(e)}")

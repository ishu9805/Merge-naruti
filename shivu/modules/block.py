from . import sudo_filter
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram import Client, filters
import time

from .watchers import block_watcher
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

dic1 = {}
dic2 = {}
t_block = {}
bdb = db.block

def temp_block(user_id):
    if user_id in t_block:
        if int(time.time() - t_block[user_id]) > 270:
            t_block.pop(user_id)
    return user_id in t_block

@app.on_message(filters.group, group=block_watcher)
async def block_cwf(_, m: Message):
    if m.from_user is None:
        return

    user_id = m.from_user.id

    if user_id in t_block:
        if time.time() - t_block[user_id] < 270:
            return
        t_block.pop(user_id)

    current_time = time.time()

    if user_id in dic1:
        if current_time - dic1[user_id] <= 1:
            dic2[user_id] = dic2.get(user_id, 0) + 1
            if dic2[user_id] >= 15:
                t_block[user_id] = current_time
                dic2[user_id] = 0
                #txt = "."
                txt = "🚫 __You've been temporarily blocked!__\nYou're sending too many messages too quickly. Please slow down and try again in **5 minutes**."
                await m.reply(txt)
        else:
            dic2[user_id] = 0
    else:
        dic2[user_id] = 0

    dic1[user_id] = current_time

async def block(user_id):
    await bdb.insert_one({'user_id': user_id})

async def is_blocked(user_id) -> bool:
    x = await bdb.find_one({'user_id': user_id})
    return bool(x)

async def unblock(user_id):
    await bdb.delete_one({'user_id': user_id})

async def save_block_reason(user_id: int, reason: str):
    await bdb.update_one(
        {'user_id': user_id},
        {'$set': {'reason': reason}},
        upsert=True
    )

async def get_block_reason(user_id):
    result = await bdb.find_one(
        {'user_id': user_id},
        {'reason': 1}
    )
    return result.get('reason') if result else None



@app.on_message(filters.command("nban") & sudo_filter)
async def block_command(client, message: Message):
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    else:
        try:
            target_id = int(message.text.split()[1])
        except:
            return await message.reply("Please either reply to a user's message or provide their user ID.")

    reason = None
    if "-r" in message.text:
        reason_start_index = message.text.index("-r") + 3
        reason = message.text[reason_start_index:].strip()

    if await is_blocked(target_id):
        block_reason = await get_block_reason(target_id)
        return await message.reply(
            f"ℹ️ *User Already Blocked!*\n"
            f"This user is already on the block list.\n"
            f"- **Reason:** `{block_reason if block_reason else 'Not specified'}`",
            parse_mode="Markdown"
        )

    await block(target_id)

    if reason:
        await save_block_reason(target_id, reason)

    await message.reply(
        f"✅ __User Blocked Successfully!__\n"
        f"The user has been blocked permanently.\n"
        f"- **Reason:** `{reason if reason else 'Not specified'}`",
        parse_mode="Markdown"
    )

@app.on_message(filters.command("nunban") & sudo_filter)
async def unblock_command(client, message: Message):
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    else:
        try:
            target_id = int(message.text.split()[1])
        except:
            return await message.reply("Please either reply to a user's message or provide their user ID.")

    if not await is_blocked(target_id):
        return await message.reply(
            "ℹ️ __User Not Blocked!__\n"
            "This user is not currently on the block list.",
            parse_mode="Markdown"
        )

    await unblock(target_id)
    await message.reply(
        "✅ __User Unblocked Successfully!__\n"
        "The user has been removed from the block list and can now interact with the bot again.",
        parse_mode="Markdown"
    )

@app.on_message(filters.command("nbanlist") & sudo_filter)
async def blocklist_command(client: Client, message: Message):
    blocked_users = await db.block.find().to_list(None)
    if not blocked_users:
        return await message.reply(
            "📜 __Blocked Users List__\n"
            "There are no users currently blocked. Great job keeping things clean! 🎉",
            parse_mode="Markdown"
        )

    user_list = "\n".join(
        [
            f"User ID: {user['user_id']} (Reason: {user.get('reason', 'Not specified')})"
            for user in blocked_users
        ]
    )
    text = (
        "📜 __Blocked Users List__\n"
        "Here are the users currently blocked:\n"
        f"```\n{user_list}\n```"
    )
    await message.reply(
        text,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Close", callback_data="close_blocklist")]]
        ),
        parse_mode="Markdown"
    )

block_dic = {}

def block_dec(func):
    async def wrapper(client, message: Message):
        user_id = message.from_user.id
        if await is_blocked(user_id) or user_id in block_dic:
            reason = await get_block_reason(user_id)
            if reason:
                return await message.reply(f"You are blocked from using this bot.\nReason: {reason}")
            else:
                return await message.reply("You are blocked from using this bot. The reason was not specified.")
        return await func(client, message)
    return wrapper

def block_cbq(func):
    async def wrapper(client, callback_query: CallbackQuery):
        user_id = callback_query.from_user.id
        if await is_blocked(user_id) or user_id in block_dic:
            reason = await get_block_reason(user_id)
            if reason:
                return await callback_query.answer(f"You are blocked from using this bot.\nReason: {reason}", show_alert=True)
            else:
                return await callback_query.answer("You are blocked from using this bot. The reason was not specified.", show_alert=True)
        return await func(client, callback_query)
    return wrapper

async def get_all_blocked_users():
    blocked_users = await db.block.find().to_list(None)
    return [user['user_id'] for user in blocked_users]


@app.on_callback_query(filters.regex("close_blocklist") & sudo_filter)
async def close_callback(client: Client, callback_query: CallbackQuery):
    command_user_id = callback_query.message.reply_to_message.from_user.id
    caller_user_id = callback_query.from_user.id

    if command_user_id != caller_user_id:
        reason = await get_block_reason(caller_user_id)
        reason_text = f"Reason: {reason}" if reason else "Reason: Not specified."
        await callback_query.answer(f"Who are you to ask me to close this?\n{reason_text}", show_alert=True)
        return

    await callback_query.message.delete()
    await callback_query.answer("Closed", show_alert=False)

from telegram import Update
from telegram.ext import CallbackContext

def block_dec_ptb(func):
    async def wrapper(update: Update, context: CallbackContext):
        user_id = update.effective_user.id if update.effective_user else None
        if user_id and (await is_blocked(user_id) or user_id in block_dic):
            return
        return await func(update, context)
    return wrapper

def block_cbq_ptb(func):
    async def wrapper(update: Update, context: CallbackContext):
        user_id = update.effective_user.id if update.effective_user else None
        if user_id and (await is_blocked(user_id) or user_id in block_dic):
            reason = await get_block_reason(user_id)
            reason_text = f"Reason: {reason}" if reason else "Reason: Not specified."
            await update.callback_query.answer(
                f"You are blocked from using this bot.\n{reason_text}",
                show_alert=True
            )
            return
        return await func(update, context)
    return wrapper

def block_inl_ptb(func):
    async def wrapper(update: Update, context: CallbackContext):
        user_id = update.effective_user.id if update.effective_user else None
        if user_id and (await is_blocked(user_id) or user_id in block_dic):
            reason = await get_block_reason(user_id)
            reason_text = f"Reason: {reason}" if reason else "Reason: Not specified."
            await update.inline_query.answer(f"You are blocked from using this bot.\n{reason_text}")
            return
        return await func(update, context)
    return wrapper

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from . import dev_filter, sudo_filter
#from shivu import OWNER_ID
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

sudb = db.sudo
devb = db.dev
uploaderdb = db.uploader

NEGLECTED_IDS = {}

@app.on_message(filters.command("addsudo") & dev_filter)
async def add_sudo(client, message: Message):
    if message.reply_to_message:
        tar = message.reply_to_message.from_user.id
    else:
        try:
            tar = int(message.text.split()[1])
        except Exception:
            return await message.reply_text("Please reply to a user or provide a valid user ID.")

    if tar in NEGLECTED_IDS:
        return await message.reply_text("This user cannot be added to the sudo list.")

    if await sudb.find_one({'user_id': tar}):
        return await message.reply_text("This user is already a sudo user.")

    try:
        await sudb.insert_one({'user_id': tar})
        await message.reply_text("User has been successfully added to the sudo list.")
    except Exception:
        await message.reply_text("Failed to add the user to the sudo list.")

@app.on_message(filters.command("rmsudo") & dev_filter)
async def remove_sudo(client, message: Message):
    if message.reply_to_message:
        tar = message.reply_to_message.from_user.id
    else:
        try:
            tar = int(message.text.split()[1])
        except Exception:
            return await message.reply_text("Please reply to a user or provide a valid user ID.")

    if not await sudb.find_one({'user_id': tar}):
        return await message.reply_text("This user is not a sudo user.")

    try:
        await sudb.delete_one({'user_id': tar})
        await message.reply_text("User has been successfully removed from the sudo list.")
    except Exception:
        await message.reply_text("Failed to remove the user from the sudo list.")

@app.on_message(filters.command("adddev") & filters.user([6902029663]))
async def add_dev(client, message: Message):
    if message.reply_to_message:
        tar = message.reply_to_message.from_user.id
    else:
        try:
            tar = int(message.text.split()[1])
        except Exception:
            return await message.reply_text("Please reply to a user or provide a valid user ID.")

    if tar in NEGLECTED_IDS:
        return await message.reply_text("This user cannot be added to the developer list.")

    try:
        await devb.insert_one({'user_id': tar})
        await message.reply_text("User has been successfully added to the developer list.")
    except Exception:
        await message.reply_text("Failed to add the user to the developer list.")

@app.on_message(filters.command("rmdev") & dev_filter)
async def remove_dev(client, message: Message):
    if message.reply_to_message:
        tar = message.reply_to_message.from_user.id
    else:
        try:
            tar = int(message.text.split()[1])
        except Exception:
            return await message.reply_text("Please reply to a user or provide a valid user ID.")

    if tar == 7378476666:
        return await message.reply_text("This developer cannot be removed.")

    if not await devb.find_one({'user_id': tar}):
        return await message.reply_text("This user is not a developer.")

    try:
        await devb.delete_one({'user_id': tar})
        await message.reply_text("User has been successfully removed from the developer list.")
    except Exception:
        await message.reply_text("Failed to remove the user from the developer list.")

@app.on_message(filters.command("adduploader") & dev_filter)
async def add_uploader(client, message: Message):
    if message.reply_to_message:
        tar = message.reply_to_message.from_user.id
    else:
        try:
            tar = int(message.text.split()[1])
        except Exception:
            return await message.reply_text("Please reply to a user or provide a valid user ID.")

    if tar in NEGLECTED_IDS:
        return await message.reply_text("This user cannot be added to the uploader list.")

    if await uploaderdb.find_one({'user_id': tar}):
        return await message.reply_text("This user is already an uploader.")

    try:
        await uploaderdb.insert_one({'user_id': tar})
        await message.reply_text("User has been successfully added to the uploader list.")
    except Exception:
        await message.reply_text("Failed to add the user to the uploader list.")

@app.on_message(filters.command("rmuploader") & sudo_filter)
async def remove_uploader(client, message: Message):
    if message.reply_to_message:
        tar = message.reply_to_message.from_user.id
    else:
        try:
            tar = int(message.text.split()[1])
        except Exception:
            return await message.reply_text("Please reply to a user or provide a valid user ID.")

    if not await uploaderdb.find_one({'user_id': tar}):
        return await message.reply_text("This user is not an uploader.")

    try:
        await uploaderdb.delete_one({'user_id': tar})
        await message.reply_text("User has been successfully removed from the uploader list.")
    except Exception:
        await message.reply_text("Failed to remove the user from the uploader list.")

@app.on_message(filters.command("sudolist") & sudo_filter)
async def sudo_list(client, message: Message):
    try:
        sudo_list = await sudb.distinct('user_id')
        if not sudo_list:
            return await message.reply_text("No sudo users found.")

        user_list = []
        for user_id in sudo_list:
            user_data = await user_collection.find_one({'id': user_id})
            if user_data:
                first_name = user_data.get('first_name', 'Unknown')
                user_list.append(f"• {first_name} (`{user_id}`)")
            else:
                user_list.append(f"• User ID: {user_id} (`{user_id}`)")

        response_text = f'Total sudo users: {len(user_list)}\n\n' + '\n'.join(user_list)
        
        await message.reply_text(response_text)
    except Exception as e:
        await message.reply_text(f"An error occurred while fetching the sudo list: {str(e)}")

@app.on_message(filters.command("devlist") & dev_filter)
async def dev_list(client, message: Message):
    try:
        dev_users_list = await devb.distinct('user_id')
        if not dev_users_list:
            return await message.reply_text("No developers found.")

        user_list = []
        for user_id in dev_users_list:
            user_data = await user_collection.find_one({'id': user_id})
            if user_data:
                first_name = user_data.get('first_name', 'Unknown')
                user_list.append(f"• {first_name} (`{user_id}`)")
            else:
                user_list.append(f"• User ID: {user_id} (`{user_id}`)")

        response_text = f'Total developers: {len(user_list)}\n\n' + '\n'.join(user_list)
        
        await message.reply_text(response_text)
    except Exception as e:
        await message.reply_text(f"An error occurred while fetching the developer list: {str(e)}")

@app.on_message(filters.command("uploaderlist") & sudo_filter)
async def uploader_list(client, message: Message):
    try:
        uploader_users_list = await uploaderdb.distinct('user_id')
        if not uploader_users_list:
            return await message.reply_text("No uploaders found.")

        user_list = []
        for user_id in uploader_users_list:
            user_data = await user_collection.find_one({'id': user_id})
            if user_data:
                first_name = user_data.get('first_name', 'Unknown')
                user_list.append(f"• {first_name} (`{user_id}`)")
            else:
                user_list.append(f"• User ID: {user_id} (`{user_id}`)")

        response_text = f'Total uploaders: {len(user_list)}\n\n' + '\n'.join(user_list)
        
        await message.reply_text(response_text)
    except Exception as e:
        await message.reply_text(f"An error occurred while fetching the uploader list: {str(e)}")


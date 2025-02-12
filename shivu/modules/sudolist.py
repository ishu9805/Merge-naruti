from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from . import app, dev_filter, sudo_filter, db, user_collection
from shivu import OWNER_ID

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

@app.on_message(filters.command("adddev") & (filters.user(OWNER_ID)))
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

    if tar == 7455169019:
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
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Close", callback_data=f"sud_clos_{message.from_user.id}")]]
        )
        await message.reply_text(response_text, reply_markup=keyboard)
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
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Close", callback_data=f"sud_clos_{message.from_user.id}")]]
        )
        await message.reply_text(response_text, reply_markup=keyboard)
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
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Close", callback_data=f"sud_clos_{message.from_user.id}")]]
        )
        await message.reply_text(response_text, reply_markup=keyboard)
    except Exception as e:
        await message.reply_text(f"An error occurred while fetching the uploader list: {str(e)}")

@app.on_callback_query(filters.regex(r"sud_clos_\d+"))
async def close_callback(client, callback_query: CallbackQuery):
    callback_user_id = int(callback_query.data.split("_")[-1])
    if callback_query.from_user.id != callback_user_id:
        return await callback_query.answer("This button is not for you!", show_alert=True)
    await callback_query.message.delete()

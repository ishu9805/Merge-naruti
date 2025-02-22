import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, Message, CallbackQuery

from . import user_collection, app
from .block import block_dec, block_cbq, temp_block

@app.on_message(filters.command("fav"))
@block_dec
async def fav(client: Client, message: Message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    if len(message.command) < 2:
        await message.reply_text("❌ Please provide a character ID.")
        return

    character_id = message.command[1]
    user = await user_collection.find_one({'id': user_id})
    if not user:
        await message.reply_text("❌ You don't have any characters yet.")
        return

    character = next((c for c in user['characters'] if c['id'] == character_id), None)
    if not character:
        await message.reply_text("❌ This character is not in your list.")
        return

    keyboard = IKM(
        [
            
            [
                IKB("✔️ Confirm", callback_data=f'fconfirm_{user_id}_{character_id}'),
                IKB("❌ Cancel", callback_data=f'fcancel_{user_id}_{character_id}')
            ]
        ]
    )

    if character.get("img_url"):
        await message.reply_photo(
            photo=character["img_url"],
            caption=f"Do you want to make {character['name']} your favorite character?",
            reply_markup=keyboard
        )
    elif character.get("vid_url"):
        await message.reply_video(
            video=character["vid_url"],
            caption=f"Do you want to make {character['name']} your favorite character?",
            reply_markup=keyboard
        )
    else:
        await message.reply_text(
            f"Do you want to make {character['name']} your favorite character?",
            reply_markup=keyboard
        )


async def handle_confirmation(user_id, character_id):
    user = await user_collection.find_one({'id': user_id})
    if not user:
        await app.send_message(user_id, "❌ You don't have any characters yet.")
        return

    character = next((c for c in user['characters'] if c['id'] == character_id), None)
    if not character:
        await app.send_message(user_id, "❌ This character is not in your list.")
        return

    user['favorites'] = [character_id]
    await user_collection.update_one({'id': user_id}, {'$set': {'favorites': user['favorites']}})
    await app.send_message(user_id, f"✅ {character['name']} is now your favorite character!")


@app.on_callback_query(filters.regex(r'^(fconfirm_|fcancel_)'))
@block_cbq
async def button(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data
    action, cmd_user_id, character_id = data.split('_')

    if int(cmd_user_id) != user_id:
        await callback_query.answer("❌ This action is not for you!", show_alert=True)
        return

    if data.startswith("fconfirm"):
        await handle_confirmation(user_id, character_id)
        await callback_query.message.edit_text("✅ Favorite character updated!")
    elif data.startswith("fcancel"):
        await callback_query.message.edit_text("❌ Operation canceled.")

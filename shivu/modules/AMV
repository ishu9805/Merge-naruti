from pyrogram import filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    InputMediaVideo
)
from shivu import shivuups as app
from shivu import collectionps as collection
import re

AMV_CACHE = {}

def amv_keyboard(index, total):
    buttons = []
    if index > 0:
        buttons.append(
            InlineKeyboardButton("⬅ Previous", callback_data=f"amv_{index}")
        )
    if index < total - 1:
        buttons.append(
            InlineKeyboardButton("Next ➡", callback_data=f"amv_{index + 2}")
        )
    return InlineKeyboardMarkup([buttons])

@app.on_message(filters.command("amv"))
async def amv_command(client, message: Message):

    args = message.text.split(maxsplit=2)

    query = {}
    title = "All AMV Videos"

    if len(args) >= 3:
        mode = args[1].lower()
        search = args[2].strip()

        regex = {"$regex": re.escape(search), "$options": "i"}

        if mode == "name":
            query["name"] = regex
            title = f"AMV by Name: {search}"

        elif mode == "anime":
            query["anime"] = regex
            title = f"AMV by Anime: {search}"

    query["vid_url"] = {"$exists": True, "$ne": ""}

    cursor = collection.find(
        query,
        {"name": 1, "anime": 1, "rarity": 1, "vid_url": 1}
    )

    videos = await cursor.to_list(length=None)

    if not videos:
        return await message.reply_text("No AMV videos found.")

    chat_id = message.chat.id
    AMV_CACHE[chat_id] = videos

    char = videos[0]

    caption = (
        f"{title}\n\n"
        f"Name: {char.get('name')}\n"
        f"Anime: {char.get('anime')}\n"
        f"Rarity: {char.get('rarity')}\n"
        f"Id: {char.get('id')}\n"
        f"Index: 1/{len(videos)}"
    )

    await message.reply_video(
        video=char["vid_url"],
        caption=caption,
        reply_markup=amv_keyboard(1, len(videos))
    )

@app.on_callback_query(filters.regex(r"^amv_"))
async def amv_navigation(client, cq: CallbackQuery):

    index = int(cq.data.split("_")[1]) - 1
    chat_id = cq.message.chat.id

    videos = AMV_CACHE.get(chat_id)
    if not videos or index < 0 or index >= len(videos):
        return await cq.answer("Invalid AMV.", show_alert=True)

    char = videos[index]

    caption = (
        f"Name: {char.get('name')}\n"
        f"Anime: {char.get('anime')}\n"
        f"Rarity: {char.get('rarity')}\n"
        f"Index: {index + 1}/{len(videos)}"
    )

    await cq.message.edit_media(
        InputMediaVideo(
            media=char["vid_url"],
            caption=caption
        ),
        reply_markup=amv_keyboard(index + 1, len(videos))
    )

    await cq.answer()

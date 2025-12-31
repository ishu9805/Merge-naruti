import random
import asyncio
from pyrogram import filters
from shivu import shivuups as app, user_collectionps as user_collection

global_user_collections = {}
collection_lock = asyncio.Lock()


ALLOWED_RARITIES = {
    "⚪️ Common",
    "🟣 Rare",
    "🟡 Legendary",
    "🟢 Medium",
    "💮 Special Edition",
    "🔮 Limited Edition"
}

async def load_user_collections():
    global global_user_collections
    total_characters = 0

    async with collection_lock:
        global_user_collections.clear()

        async for user in user_collection.find().limit(15000):
            filtered_chars = [
                c for c in user.get("characters", [])
                if c.get("rarity") in ALLOWED_RARITIES
            ]

            if filtered_chars:
                global_user_collections[user["id"]] = filtered_chars
                total_characters += len(filtered_chars)

    return total_characters


@app.on_message(filters.command("cls") & filters.user(6902029663))
async def clear_collections_command(client, message):
    async with collection_lock:
        global_user_collections.clear()
    await message.reply_text("Global user collections cleared.")


@app.on_message(filters.command("loads") & filters.user(6902029663))
async def load_users_command(client, message):
    total = await load_user_collections()
    await message.reply_text(f"Loaded user collections.\nTotal characters: {total}")


@app.on_message(filters.command("sending") & filters.reply & filters.user(6902029663))
async def send_characters(client, message):

    try:
        number = int(message.command[1])
        if number <= 0:
            raise ValueError
    except (IndexError, ValueError):
        return await message.reply_text("Usage: /sending <number>")

    replied_user_id = message.reply_to_message.from_user.id

    async with collection_lock:
        all_characters = []
        for chars in global_user_collections.values():
            all_characters.extend(chars)

        if not all_characters:
            return await message.reply_text("No characters available.")

        if number > len(all_characters):
            return await message.reply_text(
                f"Only {len(all_characters)} characters available."
            )

        selected = random.sample(all_characters, number)

        selected_ids = {str(c.get("id")) for c in selected}

        await user_collection.update_one(
            {"id": replied_user_id},
            {"$push": {"characters": {"$each": selected}}},
            upsert=True
        )

        for user_id, chars in list(global_user_collections.items()):
            global_user_collections[user_id] = [
                c for c in chars if str(c.get("id")) not in selected_ids
            ]
            if not global_user_collections[user_id]:
                del global_user_collections[user_id]

    await message.reply_text(
        f"Successfully sent {number} characters."
    )

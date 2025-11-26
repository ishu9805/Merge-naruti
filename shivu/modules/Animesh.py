from pyrogram import filters
from pyrogram.types import Message
from shivu import shivuups as app
from shivu import anime_collection
from . import sudo_filter
import re

# Helper function to sanitize anime names
def sanitize_anime_name(name):
    return re.sub(r'[^\w\s-]', '', name.strip().lower())

# Add filter command
@app.on_message(filters.command("addfilter") & sudo_filter)
async def add_filter(client, message: Message):
    if len(message.command) < 3:
        await message.reply("Usage: /addfilter <anime_name> - <link>")
        return
    
    try:
        parts = message.text.split(' - ', 1)
        anime_name = parts[0].split(' ', 1)[1].strip()
        link = parts[1].strip()
    except (IndexError, ValueError):
        await message.reply("Invalid format. Use: /addfilter <anime_name> - <link>")
        return
    
    sanitized_name = sanitize_anime_name(anime_name)
    
    existing = await anime_collection.find_one({"anime_name": sanitized_name})
    if existing:
        await message.reply(f"Filter for '{anime_name}' already exists. Use /removefilter first if you want to update it.")
        return
    
    await anime_collection.insert_one({
        "original_name": anime_name,
        "anime_name": sanitized_name,
        "link": link,
        "added_by": message.from_user.id,
        "timestamp": message.date
    })
    
    await message.reply(f"✅ Successfully added filter for '{anime_name}'")

# Get anime command
@app.on_message(filters.command("anime"))
async def get_anime(client, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /anime <anime_name>")
        return
    
    anime_name = ' '.join(message.command[1:])
    sanitized_name = sanitize_anime_name(anime_name)
    
    result = await anime_collection.find_one({"anime_name": sanitized_name})
    
    if result:
        response = (
            f"**{result['original_name']}**\n\n"
            f"🔗 Link: {result['link']}\n"
            f"📅 Added by: {(await client.get_users(result['added_by'])).mention}\n"
            f"🕒 Date added: {result['timestamp'].strftime('%Y-%m-%d %H:%M')}"
        )
        await message.reply(response, disable_web_page_preview=True)
    else:
        await message.send_message(chat_id=7377653906, text= f"'{anime_name}'. addit.")

# Remove filter command
@app.on_message(filters.command("removefilter") & sudo_filter)
async def remove_filter(client, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /removefilter <anime_name>")
        return
    
    anime_name = ' '.join(message.command[1:])
    sanitized_name = sanitize_anime_name(anime_name)
    
    result = await anime_collection.delete_one({"anime_name": sanitized_name})
    
    if result.deleted_count > 0:
        await message.reply(f"✅ Successfully removed filter for '{anime_name}'")
    else:
        await message.reply(f"No filter found for '{anime_name}'")

# List all filters command
@app.on_message(filters.command("listfilters") & sudo_filter)
async def list_filters(client, message: Message):
    count = await anime_collection.count_documents({})
    if count == 0:
        await message.reply("No anime filters have been added yet.")
        return
    
    response = "📚 **List of Anime Filters:**\n\n"
    async for item in anime_collection.find().sort("original_name", 1):
        response += f"• {item['original_name']}\n"
        if len(response) > 3500:  # Prevent hitting message length limit
            await message.reply(response)
            response = ""
    
    if response:
        await message.reply(response)

# Start command
@app.on_message(filters.command("aastart"))
async def start(client, message: Message):
    help_text = (
        "🤖 **Anime Filter Bot**\n\n"
        "**Commands:**\n"
        "/addfilter <name> - <link> - Add new anime filter (Admin only)\n"
        "/anime <name> - Get anime link\n"
        "/removefilter <name> - Remove anime filter (Admin only)\n"
        "/listfilters - List all available anime\n"
        "\nUse the bot to quickly share anime links!"
    )
    await message.reply(help_text)

print("Anime Filter Bot is running...")

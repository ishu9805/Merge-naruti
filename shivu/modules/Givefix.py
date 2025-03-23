import random
from pyrogram import Client, filters
from shivu import shivuups as app, user_collectionps as user_collection

# Global variable to store all user collections
global_user_collections = {}

# Function to load all user collections into the global variable
# Function to load up to 15,000 user collections into the global variable
async def load_user_collections():
    total_characters = 0
    async for user in user_collection.find().limit(15000):  # Limit to 15,000 documents
        characters = user.get('characters', [])
        global_user_collections[user['id']] = characters
        total_characters += len(characters)
    return total_characters
    
@app.on_message(filters.command("cls") & filters.user(7378476666))
async def clear_collections_command(client, message):
    global global_user_collections
    async with collection_lock:  # Ensure thread-safe access
        global_user_collections.clear()
    await message.reply_text("Global user collections have been successfully cleared.")
    
# Command to load all user collections into the global document
@app.on_message(filters.command("loads") & filters.user(7378476666))
async def load_users_command(client, message):
    total_characters = await load_user_collections()
    await message.reply_text(f"User collections loaded successfully. Total characters loaded: {total_characters}")

# Command to give characters to the replied user
@app.on_message(filters.command("sending") & filters.reply & filters.user(7378476666))
async def send_characters(client, message):
    try:
        # Get the number of characters to send from the command arguments
        number_of_characters = int(message.command[1])
    except (IndexError, ValueError):
        await message.reply_text("Please provide a valid number of characters to send. Example: /sending 5")
        return

    # Get the replied user's ID
    replied_user_id = message.reply_to_message.from_user.id

    # Check if there are characters available in the global collection
    all_characters = [char for chars in global_user_collections.values() for char in chars]
    if not all_characters:
        await message.reply_text("No characters available in the global collection.")
        return

    # Check if the number of requested characters is available
    if number_of_characters > len(all_characters):
        await message.reply_text(f"Only {len(all_characters)} characters are available.")
        return

    # Randomly select the specified number of characters
    characters_to_send = random.sample(all_characters, number_of_characters)

    # Update the replied user's collection in the database
    await user_collection.update_one(
        {'id': replied_user_id},
        {'$push': {'characters': {'$each': characters_to_send}}},
        upsert=True
    )

    # Remove the sent characters from the global document to avoid duplicates
    for char in characters_to_send:
        for user_id, chars in global_user_collections.items():
            if char in chars:
                chars.remove(char)
                break
    await message.reply_text(f"Successfully sent {number_of_characters} characters to the replied user.")

# Start the bot

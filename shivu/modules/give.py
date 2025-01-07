from telegram import Update
from itertools import groupby
import math
from html import escape 
import random

from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from shivu import collection, user_collection, application, PARTNER, ban_collection


async def give_character_reply(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in PARTNER:
        await update.message.reply_text('Ask My Owner...')
        return

    try:
        # Check if the reply is to a user message
        if not update.message.reply_to_message or not update.message.reply_to_message.from_user:
            await update.message.reply_text('Reply to a user message to give them a character.')
            return

        args = context.args
        if len(args) != 1:
            await update.message.reply_text('Incorrect format. Please use: /give_character_reply character_id')
            return

        character_id = args[0]
        user_id = update.message.reply_to_message.from_user.id

        # Check if the character exists
        character = await collection.find_one({'id': character_id})
        if not character:
            await update.message.reply_text('Character not found.')
            return

        # Update the user's character list with the given character
        await user_collection.update_one(
            {'id': user_id},
            {'$push': {'characters': character}}
        )
        await user_count.update_one(
            {'user_id': user_id},
            {'$inc': {'ccount': 1}},
            upsert=True
        )

        await update.message.reply_text(f'Character "{character["name"]}" has been given to user with ID {user_id}.')
    except Exception as e:
        await update.message.reply_text(f'An error occurred: {str(e)}')

async def rarities(update: Update, context: CallbackContext):

    user_id = update.effective_user.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        # If the user is banned, do nothing
        return
    else:
        pass
    characters_cursor = collection.find({})  # Get the cursor for all characters

    rarity_counts = {
        "⚪️ Common": 0,
        "🟣 Rare": 0,
        "🟡 Legendary": 0,
        "🟢 Medium": 0,
        "💮 Special Edition": 0,
        "🔮 Limited Edition": 0,
        "💸 Premium Edition": 0,
        "🌤 Summer": 0,
        "🎐 Celestial": 0,
        "❄️ Winter": 0,
        "💝 Valentine": 0,
        "🎃 Halloween": 0,
        "🎄 Christmas Special": 0,
        "🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐": 0,
        "🎭 Cosplay Master 🎭": 0
    }

    async for character in characters_cursor:  # Iterate over the cursor asynchronously
        rarity = character.get('rarity')
        print(f"Encountered rarity: '{rarity}'")  # Print out the rarity value
        if rarity in rarity_counts:
            rarity_counts[rarity] += 1
        else:
            print(f"Unknown rarity: '{rarity}'")

    rarity_message = "<b>Rarity Counts:</b>\n"
    for rarity, count in rarity_counts.items():
        rarity_message += f"{rarity}: {count}\n"

    await update.message.reply_text(rarity_message, parse_mode='HTML')

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackQueryHandler
from telegram import Update
from telegram.ext import CallbackContext



# Helper function to generate response message and buttons
async def generate_character_page_message(name_to_search, page=0):
    characters_cursor = collection.find({"name": {"$regex": f".*{name_to_search}.*", "$options": "i"}})

    found_characters = []
    async for character in characters_cursor.skip(page * 10).limit(10):
        found_characters.append(character)

    if not found_characters:
        return None, None  # No results

    response_message = "<b>Found Characters:</b>\n"
    for character in found_characters:
        response_message += f"ID: {character['id']}\n"
        response_message += f"Name: {character['name']}\n"
        response_message += f"Rarity: {character['rarity']}\n\n"

    # Pagination buttons
    total_characters = await collection.count_documents({"name": {"$regex": f".*{name_to_search}.*", "$options": "i"}})
    total_pages = (total_characters // 10) + (1 if total_characters % 10 > 0 else 0)

    buttons = [
        [
            InlineKeyboardButton("⬅️ Previous", callback_data=f"prev:{name_to_search}:{page - 1}") if page > 0 else InlineKeyboardButton("⬅️ Previous", callback_data="no_previous"),
            InlineKeyboardButton("Next ➡️", callback_data=f"next:{name_to_search}:{page + 1}") if page + 1 < total_pages else InlineKeyboardButton("No More Pages", callback_data="no_more_pages")
        ]
    ]
    
    return response_message, InlineKeyboardMarkup(buttons)

# Command handler to search for characters
async def search_character(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # Check if the user is banned (you can adjust this logic as per your needs)
    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        return

    name_to_search = " ".join(context.args).strip()

    if not name_to_search:
        await update.message.reply_text("Please provide a name to search for.")
        return

    # Generate the first page message
    message, buttons = await generate_character_page_message(name_to_search, page=0)
    
    if message is None:
        await update.message.reply_text("No characters found with that name.")
        return

    # Send the first page of results
    await update.message.reply_text(message, parse_mode='HTML', reply_markup=buttons)

# Handler for the callback query when clicking on 'Next' or 'Previous' button
async def handle_pagination(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split(":")
    
    if len(data) < 3:
        return

    action, name_to_search, page = data
    page = int(page)

    # Generate the page message
    message, buttons = await generate_character_page_message(name_to_search, page)

    if message is None:
        await query.answer("No more characters found.")
        return

    # Edit the message with new page content and buttons
    await query.edit_message_text(message, parse_mode='HTML', reply_markup=buttons)

# Add handlers to the application
application.add_handler(CommandHandler("sips", search_character))
application.add_handler(CallbackQueryHandler(handle_pagination, pattern="^(next|prev):"))




async def remove_character(update: Update, context: CallbackContext):

    
    if str(update.effective_user.id) not in PARTNER:
        await update.message.reply_text('Ask My Owner...')
        return

    try:
        # Check if the command format is correct
        args = context.args
        if len(args) != 2:
            await update.message.reply_text('Incorrect format. Please use: /remove_character user_id character_id')
            return

        user_id = int(args[0])
        character_id = args[1]

        # Check if the user exists
        user = await user_collection.find_one({'id': user_id})
        if not user:
            await update.message.reply_text('User not found.')
            return

        # Check if the character exists in the user's collection
        character_index = None
        for i, character in enumerate(user['characters']):
            if character['id'] == character_id:
                character_index = i
                break

        if character_index is None:
            await update.message.reply_text('Character not found in user collection.')
            return

        # Remove the character from the user's collection
        del user['characters'][character_index]
        await user_collection.update_one({'id': user_id}, {'$set': {'characters': user['characters']}})
        await user_count.update_one(
            {'user_id': r_id},
            {'$inc': {'ccount': -1}},
            upsert=True
        )
        await update.message.reply_text(f'Character with ID {character_id} has been removed from user with ID {user_id}.')
    except Exception as e:
        await update.message.reply_text(f'An error occurred: {str(e)}')

async def search_character_users(update: Update, context: CallbackContext):
    # Get the character ID to search for from the command arguments
    if str(update.effective_user.id) not in PARTNER:
        await update.message.reply_text('Ask My Owner...')
        return
        
    character_id = " ".join(context.args).strip()

    if not character_id:
        await update.message.reply_text("Please provide a character ID to search for.")
        return

    # Search for users who have the character
    users_cursor = user_collection.find({"characters.id": character_id})

    found_users = []
    async for user in users_cursor:
        found_users.append(user)

    if not found_users:
        await update.message.reply_text("No users found with that character.")
        return

    # Prepare the response message with found users
    response_message = "<b>Users with character ID {}:</b>\n".format(character_id)
    for user in found_users:
        response_message += f"@{user['username']}\n"

    await update.message.reply_text(response_message, parse_mode='HTML')


async def sync_user_characters(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in PARTNER:
        await update.message.reply_text('Ask My Owner...')
        return

    try:
        characters_cursor = collection.find({}, {"id": 1, "name": 1, "rarity": 1, "anime": 1, "img_url": 1})
        character_dict = {character["id"]: {"name": character["name"], "rarity": character["rarity"], "anime": character["anime"], "img_url": character["img_url"]} async for character in characters_cursor}

        users_cursor = user_collection.find()
        count = 0
        async for user in users_cursor:
            user_id = user["id"]
            characters = user.get("characters", [])

            for character in characters:
                if character["id"] in character_dict:
                    character["name"] = character_dict[character["id"]]["name"]
                    character["rarity"] = character_dict[character["id"]]["rarity"]
                    character["anime"] = character_dict[character["id"]]["anime"]
                    character["img_url"] = character_dict[character["id"]]["img_url"]

            await user_collection.update_one({"id": user_id}, {"$set": {"characters": characters}})
            count += 1

        await update.message.reply_text(f"User characters synced with collection. {count} users updated.")
    except Exception as e:
        await update.message.reply_text(f"Error syncing user characters: {e}")


async def check_duplicate_ids(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in PARTNER:
        await update.message.reply_text('Ask My Owner...')
        return

    characters_cursor = collection.find({}, {"id": 1})
    ids = [character["id"] async for character in characters_cursor]

    duplicate_ids = [id for id, count in collections.Counter(ids).items() if count > 1]

    if duplicate_ids:
        await update.message.reply_text(f"Duplicate IDs found: {', '.join(duplicate_ids)}")
    else:
        await update.message.reply_text("No duplicate IDs found.")


application.add_handler(CommandHandler("duplicate", check_duplicate_ids))
application.add_handler(CommandHandler("sync", sync_user_characters))
application.add_handler(CommandHandler("whi", search_character_users))
application.add_handler(CommandHandler("takec", remove_character))


application.add_handler(CommandHandler("rarities", rarities))
GIVE_CHARACTER_REPLY_HANDLER = CommandHandler('givec', give_character_reply, block=False)
application.add_handler(GIVE_CHARACTER_REPLY_HANDLER)

from telegram import Update
from itertools import groupby
import math
from html import escape 
import random

from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
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

# Lock to ensure thread-safe access to the global variable
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
        "🎭 Cosplay Master 🎭": 0,
        "🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣": 0,
        "🧧 𝙀𝙫𝙚𝙣𝙩𝙨": 0
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
    
application.add_handler(CommandHandler("rarities", rarities))

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
        rarity = character['rarity']
        '''await user_count.update_one(
            {'user_id': user_id},
            {'$inc': {f'rarity_count.{rarity}': 1}},
            upsert=True
        )
        '''
        

        await update.message.reply_text(f'Character "{character["name"]}" has been given to user with ID {user_id}.')
    except Exception as e:
        await update.message.reply_text(f'An error occurred: {str(e)}')



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


import logging
from pyrogram import Client, filters
from pyrogram.errors import UserIsBlocked
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from . import sudo_filter, dev_filter
from shivu import LOG_CHANNEL as LOG_CHAT_ID
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


CHARACTERS_FIELD = "characters"
ID_FIELD = "id"

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def give_character(receiver_id, character_id):
    """
    Give a character to a user.
    """
    try:
        character = await collection.find_one({ID_FIELD: character_id})
        if not character:
            raise ValueError("Character not found.")

        await user_collection.update_one(
            {ID_FIELD: receiver_id},
            {'$push': {CHARACTERS_FIELD: character}}
        )

        # Updated caption format
        caption = (
            f"Name: {character['name']}\n"
            f"Anime: {character['anime']}\n"
            f"ID: {character[ID_FIELD]}\n"
            f"Rarity: {character.get('rarity', 'Unknown')}"
        )

        return character['img_url'], caption, character['name']
    except PyMongoError as e:
        logger.error(f"Database error in give_character: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in give_character: {e}")
        raise

@app.on_message(filters.command(["givec"]) & sudo_filter)
async def give_character_command(client, message):
    """
    Command to give a character to a user.
    """
    if not message.reply_to_message:
        await message.reply_text("You need to reply to a user's message to give a character!")
        return

    try:
        # Parse the command arguments
        args = message.text.split(maxsplit=2)  # Split into 3 parts: /give, id, optional_message
        if len(args) < 2:
            await message.reply_text("Please provide a character ID.")
            return

        character_id = str(args[1])
        optional_message = args[2] if len(args) > 2 else None

        receiver_id = message.reply_to_message.from_user.id
        receiver_name = message.reply_to_message.from_user.first_name
        giver_name = message.from_user.first_name

        # Give the character
        result = await give_character(receiver_id, character_id)

        if result:
            img_url, caption, character_name = result

            # Prepare the final message
            if optional_message:
                final_message = (
                    f"{optional_message}\n\n"
                    f"Here's your Prize:\n"
                    f"{character_id} - {character_name}"
                )
            else:
                final_message = f"Successfully Given To {receiver_id}\n\n{caption}"

            # Send the image and message
            await message.reply_photo(photo=img_url, caption=final_message)

            # Send a message to the receiver
            if optional_message:
                try:
                    await client.send_message(receiver_id, final_message)
                except UserIsBlocked:
                    logger.warning(f"Bot is blocked by user {receiver_id}. Skipping message to receiver.")
                    pass  # Skip sending the message if the bot is blocked

            # Log the give action
            log_message = f"{giver_name} gave character {character_id} ({character_name}) to {receiver_name}."
            try:
                await client.send_message(LOG_CHAT_ID, log_message)
            except UserIsBlocked:
                logger.warning(f"Bot is blocked by the user. Skipping log message to {LOG_CHAT_ID}.")
                pass  # Skip sending the log if the bot is blocked

    except IndexError:
        await message.reply_text("Please provide a character ID.")
    except ValueError as e:
        await message.reply_text(str(e))
    except Exception as e:
        logger.error(f"Error in give_character_command: {e}")
        await message.reply_text("An error occurred while processing the command.")


async def kill_character(receiver_id, character_id):
    """
    Remove a character from a user's collection.
    """
    try:
        character = await collection.find_one({ID_FIELD: character_id})
        if not character:
            raise ValueError("Character not found.")

        await user_collection.update_one(
            {ID_FIELD: receiver_id},
            {'$pull': {CHARACTERS_FIELD: {ID_FIELD: character_id}}},
            upsert=True
        )
        return f"Successfully removed character {character_id} from user {receiver_id}."
    except PyMongoError as e:
        logger.error(f"Database error in kill_character: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in kill_character: {e}")
        raise

@app.on_message(filters.command(["takec"]) & sudo_filter)
async def remove_character_command(client, message):
    """
    Command to remove a character from a user.
    """
    if not message.reply_to_message:
        await message.reply_text("You need to reply to a user's message to remove a character!")
        return

    try:
        # Parse the command arguments
        args = message.text.split(maxsplit=2)  # Split into 3 parts: /takec, id, optional_message
        if len(args) < 2:
            await message.reply_text("Usage: /takec <character_id> [optional_message] (reply to a user)")
            return

        character_id = str(args[1])
        optional_message = args[2] if len(args) > 2 else None

        receiver_id = message.reply_to_message.from_user.id
        receiver_name = message.reply_to_message.from_user.first_name
        remover_name = message.from_user.first_name

        # Remove the character
        result_message = await kill_character(receiver_id, character_id)
        await message.reply_text(result_message)

        # Prepare the final message for the receiver
        if optional_message:
            final_message = (
                f"{optional_message}\n\n"
                f"Your character has been removed:\n"
                f"Character ID: {character_id}"
            )
            try:
                await client.send_message(receiver_id, final_message)
            except UserIsBlocked:
                logger.warning(f"Bot is blocked by user {receiver_id}. Skipping message to receiver.")
                pass  # Skip sending the message if the bot is blocked

        # Log the remove action
        log_message = f"{remover_name} removed character {character_id} from {receiver_name}."
        try:
            await client.send_message(LOG_CHAT_ID, log_message)
        except UserIsBlocked:
            logger.warning(f"Bot is blocked by the user. Skipping log message to {LOG_CHAT_ID}.")
            pass  # Skip sending the log if the bot is blocked

    except (IndexError, ValueError) as e:
        await message.reply_text(str(e))
    except Exception as e:
        logger.error(f"Error in remove_character_command: {e}")

        await message.reply_text("An error occurred while processing the command.")




import logging
from pyrogram import Client, filters
from pyrogram.errors import UserIsBlocked
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from . import sudo_filter, dev_filter
from shivu import LOG_CHANNEL as LOG_CHAT_ID
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

CHARACTERS_FIELD = "characters"
ID_FIELD = "id"
BALANCE_FIELD = "coins"


# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def update_balance(receiver_id, amount):
    """
    Update a user's balance (berries).
    """
    try:
        await user_collection.update_one(
            {ID_FIELD: receiver_id},
            {'$inc': {BALANCE_FIELD: amount}},
            upsert=True
        )
        return f"Successfully updated balance by {amount} berries."
    except PyMongoError as e:
        logger.error(f"Database error in update_balance: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in update_balance: {e}")
        raise


@app.on_message(filters.command(["givecoins"]) & sudo_filter)
async def give_balance_command(client, message):
    """
    Command to give berries/balance to a user.
    """
    if not message.reply_to_message:
        await message.reply_text("You need to reply to a user's message to give berries!")
        return

    try:
        # Parse the command arguments
        args = message.text.split(maxsplit=2)  # Split into 3 parts: /giveb, amount, optional_message
        if len(args) < 2:
            await message.reply_text("Usage: /giveb <amount> [optional_message] (reply to a user)")
            return

        amount = int(args[1])
        optional_message = args[2] if len(args) > 2 else None

        receiver_id = message.reply_to_message.from_user.id
        receiver_name = message.reply_to_message.from_user.first_name
        giver_name = message.from_user.first_name

        # Update the balance
        result_message = await update_balance(receiver_id, amount)
        await message.reply_text(result_message)

        # Prepare the final message for the receiver
        if optional_message:
            final_message = (
                f"{optional_message}\n\n"
                f"You have received {amount} berries."
            )
            try:
                await client.send_message(receiver_id, final_message)
            except UserIsBlocked:
                logger.warning(f"Bot is blocked by user {receiver_id}. Skipping message to receiver.")
                pass  # Skip sending the message if the bot is blocked

        # Log the give action
        log_message = f"{giver_name} gave {amount} gives to {receiver_name}."
        try:
            await client.send_message(LOG_CHAT_ID, log_message)
        except UserIsBlocked:
            logger.warning(f"Bot is blocked by the user. Skipping log message to {LOG_CHAT_ID}.")
            pass  # Skip sending the log if the bot is blocked

    except (IndexError, ValueError) as e:
        await message.reply_text("Please provide a valid amount.")
    except Exception as e:
        logger.error(f"Error in give_balance_command: {e}")
        await message.reply_text("An error occurred while processing the command.")



@app.on_message(filters.command(["takecoins"]) & sudo_filter)
async def take_balance_command(client, message):
    """
    Command to take berries/balance from a user.
    """
    if not message.reply_to_message:
        await message.reply_text("You need to reply to a user's message to take berries!")
        return

    try:
        # Parse the command arguments
        args = message.text.split(maxsplit=2)  # Split into 3 parts: /takeb, amount, optional_message
        if len(args) < 2:
            await message.reply_text("Usage: /takeb <amount> [optional_message] (reply to a user)")
            return

        amount = int(args[1])
        optional_message = args[2] if len(args) > 2 else None

        receiver_id = message.reply_to_message.from_user.id
        receiver_name = message.reply_to_message.from_user.first_name
        remover_name = message.from_user.first_name

        # Update the balance
        result_message = await update_balance(receiver_id, -amount)
        await message.reply_text(result_message)

        # Prepare the final message for the receiver
        if optional_message:
            final_message = (
                f"{optional_message}\n\n"
                f"{amount} coins have been deducted from your account."
            )
            try:
                await client.send_message(receiver_id, final_message)
            except UserIsBlocked:
                logger.warning(f"Bot is blocked by user {receiver_id}. Skipping message to receiver.")
                pass  # Skip sending the message if the bot is blocked

        # Log the take action
        log_message = f"{remover_name} took {amount} coins from {receiver_name}."
        try:
            await client.send_message(LOG_CHAT_ID, log_message)
        except UserIsBlocked:
            logger.warning(f"Bot is blocked by the user. Skipping log message to {LOG_CHAT_ID}.")
            pass  # Skip sending the log if the bot is blocked

    except (IndexError, ValueError) as e:
        await message.reply_text("Please provide a valid amount.")
    except Exception as e:
        logger.error(f"Error in take_balance_command: {e}")
        await message.reply_text("An error occurred while processing the command.")

import asyncio
import importlib
import random
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters, Application
from shivu import collection, user_collection, shivuu

from shivu import application, ban_collection



async def convert_coins_to_tokens(update: Update, context: CallbackContext) -> None:
    """
    Convert coins to tokens.

    :param update: The update object
    :param context: The context object
    :return: None
    """
    user_id = update.effective_user.id
    coins_to_convert = int(context.args[0]) if context.args else 0
    
    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        # If the user is banned, do nothing
        return
    else:
        pass

    if coins_to_convert <= 0:
        await update.message.reply_text("Invalid amount of coins to convert.")
        return

    # Get the user's current coin balance
    user_doc = await user_collection.find_one({"id": user_id})
    if user_doc is None:
        await update.message.reply_text("You don't have any coins to convert.")
        return
    current_coins = user_doc.get("coins", 0)

    # Check if the user has enough coins to convert
    if coins_to_convert > current_coins:
        await update.message.reply_text("You don't have enough coins to convert.")
        return

    # Define the conversion rate (e.g. 100 coins = 1 token)
    conversion_rate = 100

    # Calculate the number of tokens to give
    tokens = coins_to_convert // conversion_rate

    # Calculate the remaining coins that will be returned to the user
    remaining_coins = coins_to_convert % conversion_rate

    # Update the user's token balance
    await user_collection.update_one(
        {"id": user_id},
        {"$inc": {"tokens": tokens}},
        upsert=True
    )

    # Update the user's coin balance
    await user_collection.update_one(
        {"id": user_id},
        {"$inc": {"coins": -coins_to_convert + remaining_coins}},
        upsert=True
    )

    await update.message.reply_text(f"Converted {coins_to_convert - remaining_coins} coins to {tokens} tokens! You have {remaining_coins} coins remaining.")

application.add_handler(CommandHandler('convert', convert_coins_to_tokens))


async def convert_tokens_to_coins(update: Update, context: CallbackContext) -> None:
    """
    Convert tokens to coins.

    :param update: The update object
    :param context: The context object
    :return: None
    """
    user_id = update.effective_user.id
    tokens_to_convert = int(context.args[0]) if context.args else 0

    # Check if user is banned
    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        return

    if tokens_to_convert <= 0:
        await update.message.reply_text("Invalid amount of tokens to convert.")
        return

    # Get the user's current token balance
    user_doc = await user_collection.find_one({"id": user_id})
    if user_doc is None:
        await update.message.reply_text("You don't have any tokens to convert.")
        return
    current_tokens = user_doc.get("tokens", 0)

    # Check if the user has enough tokens to convert
    if tokens_to_convert > current_tokens:
        await update.message.reply_text("You don't have enough tokens to convert.")
        return

    # Define the conversion rate (e.g. 1 token = 100 coins)
    conversion_rate = 100

    # Calculate the number of coins to give
    coins = tokens_to_convert * conversion_rate

    # Update the user's coin balance
    await user_collection.update_one(
        {"id": user_id},
        {"$inc": {"coins": coins}},
        upsert=True
    )

    # Update the user's token balance
    await user_collection.update_one(
        {"id": user_id},
        {"$inc": {"tokens": -tokens_to_convert}},
        upsert=True
    )

    await update.message.reply_text(f"Converted {tokens_to_convert} tokens to {coins} coins!")

#application.add_handler(CommandHandler('tconvert', convert_tokens_to_coins))


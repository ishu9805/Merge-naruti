import asyncio
#from telethon import events, Button
#from telethon.sync import TelegramClient
from pymongo import MongoClient
from shivu import shivuu as app
from shivu import user_collection, ban_collection

import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient



# Handler for callback queries
@app.on_callback_query()
async def callback_query_handler(client, callback_query):
    try:
        data = callback_query.data

        if data == "rarity_mode:see_by_rarities":
            # Create buttons for rarities (only emojis)
            rarities_buttons = [
                [
                    InlineKeyboardButton("⚪️", callback_data="rarity:⚪️ Common"),
                    InlineKeyboardButton("🟣", callback_data="rarity:🟣 Rare"),
                    InlineKeyboardButton("🟡", callback_data="rarity:🟡 Legendary"),
                    InlineKeyboardButton("🟢", callback_data="rarity:🟢 Medium")
                ],
                [
                    InlineKeyboardButton("💮", callback_data="rarity:💮 Special Edition"),
                    InlineKeyboardButton("🔮", callback_data="rarity:🔮 Limited Edition"),
                    InlineKeyboardButton("💸", callback_data="rarity:💸 Premium Edition"),
                    InlineKeyboardButton("🎖", callback_data="rarity:🎖 Apex Lot (AUCTION)")
                ],
                [
                    InlineKeyboardButton("🌤", callback_data="rarity:🌤 Summer"),
                    InlineKeyboardButton("🎐", callback_data="rarity:🎐 Celestial"),
                    InlineKeyboardButton("☃️", callback_data="rarity:❄️ Winter"),
                    InlineKeyboardButton("💝", callback_data="rarity:💝 Valentine")
                ],
                [
                    InlineKeyboardButton("🎃", callback_data="rarity:🎃 Halloween"),
                    InlineKeyboardButton("🎄", callback_data="rarity:🎄 Christmas Special"),
                    InlineKeyboardButton("🪐", callback_data="rarity:🪐 Omniuniversal"),
                    InlineKeyboardButton("🎭", callback_data="rarity:🎭 Cosplay Master")
                ],
                [
                    InlineKeyboardButton("🎗️", callback_data="rarity:🎗️ AMV Edition")
                ]
            ]

            # Edit the message with the new buttons
            await callback_query.edit_message_caption(
                caption="Select a rarity:",
                reply_markup=InlineKeyboardMarkup(rarities_buttons)
            )

        elif data.startswith("rarity:"):
            # Update the user's rarity mode in the database
            rarity_mode = data.split(":")[1]
            await user_collection.update_one(
                {'id': callback_query.from_user.id},
                {'$set': {'rarity_mode': rarity_mode}},
                upsert=True
            )
            await callback_query.edit_message_caption(f"Your rarity mode is now set to {rarity_mode}.")

        elif data == "rarity_mode:default":
            # Set the rarity mode to "All"
            await user_collection.update_one(
                {'id': callback_query.from_user.id},
                {'$set': {'rarity_mode': 'All'}},
                upsert=True
            )
            await callback_query.edit_message_caption("Your rarity mode is now set to All.")

        # Schedule the deletion of the callback query message after 20 seconds
        await asyncio.sleep(20)
        await callback_query.message.delete()

    except Exception as e:
        await callback_query.answer("An error occurred. Please try again.", show_alert=True)
        print(f"Error handling callback query: {e}")

# Start the bot

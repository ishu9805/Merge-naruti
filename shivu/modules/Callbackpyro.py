import asyncio
#from telethon import events, Button
#from telethon.sync import TelegramClient and 
from pymongo import MongoClient
from shivu import shivuu as app
from shivu import user_collection, ban_collection


import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from shivu.modules.gift import on_gift_callback_query, on_trade_callback_query
from shivu.modules.fav import button

# Handler for callback queries
@app.on_callback_query()
async def callback_query_handler(client, callback_query):
    try:
        data = callback_query.data

        if data.startswith("sgift") or data.startswith("cgift"):
            await on_gift_callback_query(client, callback_query)
        elif data.startswith("confirm_trade_receiver:") or data.startswith("cancel_trade:"):
            await on_trade_callback_query(client, callback_query)

        elif data == "rarity_mode:see_by_rarities":
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
                    InlineKeyboardButton("🪐", callback_data="rarity:🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐"),
                    InlineKeyboardButton("🎭", callback_data="rarity:🎭 Cosplay Master 🎭")
                ],
                [
                    InlineKeyboardButton("🎗️", callback_data="rarity:🎗️ AMV Edition"),
                    InlineKetboardButton("🧧", callback_data="rarity:🧧 𝙀𝙫𝙚𝙣𝙩𝙨")
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

        elif data == "rarity_mode:All":
            # Set the rarity mode to "All"
            await user_collection.update_one(
                {'id': callback_query.from_user.id},
                {'$set': {'rarity_mode': 'All'}},
                upsert=True
            )
            await callback_query.edit_message_caption("Your rarity mode is now set to All.")

        elif data.startswith("fconfirm") or data.startswith("fcancel"):
            await button(client, callback_query)
        # Schedule the deletion of the callback query message after 20 seconds
        await asyncio.sleep(20)
        await callback_query.message.delete()

    except Exception as e:
        await callback_query.answer("An error occurred. Please try again.", show_alert=True)
        print(f"Error handling callback query: {e}")

# Start the bot

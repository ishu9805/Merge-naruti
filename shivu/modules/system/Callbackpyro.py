import asyncio
#from telethon import events, Button
#from telethon.sync import TelegramClient and 
from pymongo import MongoClient
from contextlib import suppress
from pyrogram import Client, StopPropagation, filters
from pyrogram.errors import MessageNotModified
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu.modules.gift import on_gift_callback_query, on_trade_callback_query
from shivu.modules.economy.Addshop import buy_step1, buy_confirm, buy_cancel
from shivu.modules.fav import button
from shivu.modules.Animelist import anime_letter_callback, anime_selection_callback, back_to_az_callback
from shivu.modules.Task import confirm_claim, cancel_claim # confirm_reset, cancel_reset
from shivu.modules.Pfp import approve_profile_media, reject_profile_media
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
    UPDATE_CHATps as UPDATE_CHAT_PS,
    dbps as db,
    pmusersps as pmusers,
    ban_collectionps as ban_collection,
    user_countps as user_count, 
    chat_dataps as chat_data,
)
# Handler for callback queries
@app.on_callback_query()
async def callback_query_handler(client, callback_query):
    async def safe_answer(text=None, show_alert=False):
        with suppress(Exception):
            await callback_query.answer(text=text, show_alert=show_alert)

    try:
        data = callback_query.data
        """if data.startwith("tttconfirm_"):
            await confirm_claim(client, callback_query)
        elif data.startwith("animelist_"):
            await anime_letter_callback(client, callback_query)
        elif data.startwith("anime_select_"):
            await anime_selection_callback(client, callback_query)
        elif data.startwith("back_to_az"):
            await back_to_az_callback(client, callback_query)
        elif data.startwith("tcancel_claim"):
            await cancel_claim(client, callback_query)
        elif data.startwith("confirm_reset"):
            await confirm_reset(client, callback_query)
        elif data.startwith("cancel_reset"):
            await cancel_reset(client, callback_query)"""
        
        if data.startswith("approve_pfp"):
            await approve_profile_media(client, callback_query)
            await safe_answer()
        elif data.startswith("reject_pfp"):
            await reject_profile_media(client, callback_query)
            await safe_answer()
                                
        elif data.startswith("sgift") or data.startswith("cgift"):
            await on_gift_callback_query(client, callback_query)
        elif data.startswith("confirm_trade_receiver:") or data.startswith("cancel_trade:"):
            await on_trade_callback_query(client, callback_query)

        elif data.startswith("buyshop_"):
            await buy_step1(client, callback_query)
            raise StopPropagation
        elif data.startswith("confirmbuy_"):
            await buy_confirm(client, callback_query)
            raise StopPropagation
        elif data.startswith("cancelbuy_"):
            await buy_cancel(client, callback_query)
            raise StopPropagation

        elif data == "rarity_mode:see_by_rarities":
            # Create buttons for rarities (only emojis)
            rarities_buttons = [
                [
                    InlineKeyboardButton("⚪️ ᴄᴏᴍᴍᴏɴ", callback_data="rarity:⚪️ Common"),
                    InlineKeyboardButton("🟣 ʀᴀʀᴇ", callback_data="rarity:🟣 Rare"),
                    InlineKeyboardButton("🟡 ʟᴇɢᴇɴᴅᴀʀʏ", callback_data="rarity:🟡 Legendary")
                ],
                [
                    InlineKeyboardButton("🟢 ᴍᴇᴅɪᴜᴍ", callback_data="rarity:🟢 Medium"),
                    InlineKeyboardButton("💮 ꜱᴘᴇᴄɪᴀʟ ᴇᴅɪᴛɪᴏɴ", callback_data="rarity:💮 Special Edition"),
                    InlineKeyboardButton("🔮 ʟɪᴍɪᴛᴇᴅ ᴇᴅɪᴛɪᴏɴ", callback_data="rarity:🔮 Limited Edition")
                ],
                [
                    InlineKeyboardButton("💸 ᴘʀᴇᴍɪᴜᴍ ᴇᴅɪᴛɪᴏɴ", callback_data="rarity:💸 Premium Edition"),
                    InlineKeyboardButton("🌤 ꜱᴜᴍᴍᴇʀ", callback_data="rarity:🌤 Summer"),
                    InlineKeyboardButton("🎐 ᴄᴇʟᴇꜱᴛɪᴀʟ", callback_data="rarity:🎐 Celestial")
                ],
                [
                    InlineKeyboardButton("❄️ ᴡɪɴᴛᴇʀ", callback_data="rarity:❄️ Winter"),
                    InlineKeyboardButton("💝 ᴠᴀʟᴇɴᴛɪɴᴇ", callback_data="rarity:💝 Valentine"),
                    InlineKeyboardButton("🎃 ʜᴀʟʟᴏᴡᴇᴇɴ", callback_data="rarity:🎃 Halloween")
                ],
                [
                    InlineKeyboardButton("🎄 ᴄʜʀɪꜱᴛᴍᴀꜱ ꜱᴘᴇᴄɪᴀʟ", callback_data="rarity:🎄 Christmas Special"),
                    InlineKeyboardButton("🪐 ᴏᴍɴɪᴠᴇʀꜱᴀʟ", callback_data="rarity:🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐"),
                    InlineKeyboardButton("🎭 ᴄᴏꜱᴘʟᴀʏ ᴍᴀꜱᴛᴇʀ", callback_data="rarity:🎭 Cosplay Master 🎭")
                ],
                [
                    InlineKeyboardButton("🎖 ᴀᴘᴇx ʟᴏᴛ", callback_data="rarity:🎖 Apex Lot ( AUCTION )"),
                    InlineKeyboardButton("🧧 ᴇᴠᴇɴᴛꜱ", callback_data="rarity:🧧 𝙀𝙫𝙚𝙣𝙩𝙨"),
                    InlineKeyboardButton("🍑 ᴇᴄʜʜɪ", callback_data="rarity:🍑 Echhi")
                ],
                [
                    InlineKeyboardButton("☠️ ᴅɪᴠɪɴᴇ", callback_data="rarity:☠️ 𝕯𝖎𝖛𝖎𝖓𝖊"),
                    InlineKeyboardButton("☔ ᴍᴏɴꜱᴏᴏɴ", callback_data="rarity:☔ Monsoon"),
                    InlineKeyboardButton("🪸 ᴀǫᴜᴀᴛɪᴄ", callback_data="rarity:🪸 Aquatic")
                ],
                [
                    InlineKeyboardButton("🎨 ᴀʀᴛɪꜱᴛɪᴄ", callback_data="rarity:🎨 Artistic"),
                    InlineKeyboardButton("💳 ᴠɪᴘ ꜱʟᴏᴛ", callback_data="rarity:💳 VIP SLOT"),
                    InlineKeyboardButton("👶 ᴄʜɪʙɪ", callback_data="rarity:👶 Chibi")
                ],
                [
                    InlineKeyboardButton("🏴‍☠️ ᴍᴀʀᴀᴜᴅꜱ", callback_data="rarity:🏴‍☠️ Marauds"),
                    InlineKeyboardButton("🎗️ ᴀᴍᴠ ᴇᴅɪᴛɪᴏɴ", callback_data="rarity:🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣")
                ]
            ]

            # Edit the message with the new buttons
            await callback_query.edit_message_caption(
                caption="Select a rarity:",
                reply_markup=InlineKeyboardMarkup(rarities_buttons)
            )
            await safe_answer("Choose your rarity mode.")

        elif data.startswith("rarity:"):
            # Update the user's rarity mode in the database
            rarity_mode = data.split(":")[1]
            await user_collection.update_one(
                {'id': callback_query.from_user.id},
                {'$set': {'rarity_mode': rarity_mode}},
                upsert=True
            )
            await callback_query.edit_message_caption(f"Your rarity mode is now set to {rarity_mode}.")
            await safe_answer("Rarity mode updated.")

        elif data == "rarity_mode:All":
            # Set the rarity mode to "All"
            await user_collection.update_one(
                {'id': callback_query.from_user.id},
                {'$set': {'rarity_mode': 'All'}},
                upsert=True
            )
            await callback_query.edit_message_caption("Your rarity mode is now set to All.")
            await safe_answer("Rarity mode set to All.")

        elif data.startswith("fconfirm") or data.startswith("fcancel"):
            await button(client, callback_query)
        # Schedule the deletion of the callback query message after 20 seconds
        else:
            return

    except Exception as e:
        if isinstance(e, MessageNotModified):
            await safe_answer("Nothing changed.")
            return

        await safe_answer("An error occurred. Please try again.", show_alert=True)
        print(f"Error handling callback query: {e}")

# Start the bot

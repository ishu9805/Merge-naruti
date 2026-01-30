from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext
from itertools import groupby
import math
import random
from html import escape
#from shivu import collection, user_collection, application, ban_collection
from telegram.error import BadRequest
from shivu import PARTNER
#from shivu import shivuu as app
from pyrogram import filters
from datetime import datetime, timedelta
import logging
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
from shivu.modules.lock import must_dm
from shivu.modules.fjoin import ptb_check_membership as ptbfj
from scap import capsify  # Import the capsify function

MAX_CAPTION_LENGTH = 1024

# Define rarity emojis - Updated with all requested rarities
RARITY_MAPPING = {
    "⚪️ Common": "⚪️",
    "🟣 Rare": "🟣",
    "🟡 Legendary": "🟡",
    "🟢 Medium": "🟢",
    "💮 Special Edition": "💮",
    "🔮 Limited Edition": "🔮",
    "💸 Premium Edition": "💸",
    "🌤 Summer": "🌤",
    "🎐 Celestial": "🎐",
    "❄️ Winter": "❄️",
    "💝 Valentine": "💝",
    "🎃 Halloween": "🎃",
    "🎄 Christmas Special": "🎄",
    "🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐": "🪐",
    "🎭 Cosplay Master 🎭": "🎭",
    "🧧 𝙀𝙫𝙚𝙣𝙩𝙨": "🧧",
    "🎖 Apex Lot ( AUCTION )": "🎖",
    "🍑 Echhi": "🍑",
    "☠️ 𝕯𝖎𝖛𝖎𝖓𝖊": "☠️",
    "☔ Monsoon": "☔",
    "🪸 Aquatic": "🪸",
    "🎨 Artistic": "🎨",
    "💳 VIP SLOT": "💳",
    "👶 Chibi": "👶",
    "🏴‍☠️ Marauds": "🏴‍☠️"
}

# Command to remove all PM users
async def remove_all_pm_users(update: Update, context: CallbackContext):
    # Check if user is owner
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text(capsify("You Are Not Authorized To Use This Command."))
        return
    
    # Remove all PM users
    result = await pmusers.delete_many({})
    await update.message.reply_text(capsify(f"Removed {result.deleted_count} PM Users From Database."))

#@ptbfj()
async def harem(update: Update, context: CallbackContext, page=0) -> None:
    user_id = update.effective_user.id
    
    # Check if user has started the bot in DM
    user_doc = await pmusers.find_one({'user_id': user_id})
    if not user_doc or user_doc.get('blocked', False):
        bot_username = (await context.bot.get_me()).username
        start_link = f"https://t.me/{bot_username}?start=start"
        
        message = capsify("You Need To Start Me In DM First To Use This Command.")
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(capsify("Start Bot In DM"), url=start_link)]
        ])
        
        if update.message:
            await update.message.reply_text(message, reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
        return
        
    user = await user_collection.find_one({'id': user_id})
    #user_info = await user_count.find_one({'user_id': user_id})
    """if not await is_member(user_id):
        group_link = "https://t.me/+GI1fWK_cYnA3OTFl"  # Replace with the actual group invite link
        messages = "You need to be a member of our exclusive group to use this command."
        
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("✨ Join the Group ✨", url=group_link)]]
        )
        await update.message.reply_text(messages, reply_markup=reply_markup)
        return"""
        
    if not user:
        message = capsify('You Have Not Guessed any Characters Yet..')
        if update.message:
            await update.message.reply_text(message)
        else:
            await update.callback_query.edit_message_text(message)
        return

    characters = sorted(user['characters'], key=lambda x: (x['anime'], x['id']))
    rarity_mode = await get_user_rarity_mode(user_id)
    unique_characters = list({character['id']: character for character in characters}.values())
    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}
    total_count = len(characters)
    
    if rarity_mode != 'All':
        unique_characters = [char for char in unique_characters if char.get('rarity') == rarity_mode]

    
    total_pages = math.ceil(len(unique_characters) / 20)
    if page < 0 or page >= total_pages:
        page = 0
   

    harem_message = capsify(f"{escape(update.effective_user.first_name)}'s Harem - Page {page+1}/{total_pages}\n\n")
    current_characters = unique_characters[page*15:(page+1)*20]
    current_grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])}

    for anime, characters in current_grouped_characters.items():
        harem_message += capsify(f"⌬ {anime} 〔{len(characters)}〕\n")
        for character in characters:
            rarity = character['rarity']
            count = character_counts[character['id']]
            rarity_emoji = RARITY_MAPPING.get(rarity, 'Unknown')
            harem_message += capsify(f"◈⌠{rarity_emoji}⌡ {character['id']} {character['name']} (x{count})\n")
        harem_message += "\n"

    if len(harem_message) > MAX_CAPTION_LENGTH:
        harem_message = harem_message[:MAX_CAPTION_LENGTH]

    has_animated = any(
        char.get('rarity') == "🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣" and 'vid_url' in char for char in user['characters']
    )

    keyboard = [
        [
            InlineKeyboardButton(capsify(f"🦋 Static [{total_count}]"), switch_inline_query_current_chat=f"collection.img.{user_id}"),
            InlineKeyboardButton(capsify("🎗️ 𝘼𝙈𝙑"), switch_inline_query_current_chat=f"collection.vid.{user_id}") if has_animated else None
        ]
    ]

    # Remove None values from keyboard
    keyboard[0] = [button for button in keyboard[0] if button]
    

    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(capsify("⬅️ Previous"), callback_data=f"harem:{page-1}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton(capsify("Next ➡️"), callback_data=f"harem:{page+1}"))
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton(capsify("Close"), callback_data="close")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if 'favorites' in user and user['favorites']:
            fav_character_id = user['favorites'][0]
            fav_character = next((c for c in user['characters'] if c['id'] == fav_character_id), None)
            if fav_character:
                if 'img_url' in fav_character:
                    if update.message:
                        await update.message.reply_photo(
                            photo=fav_character['img_url'], 
                            caption=harem_message, 
                            reply_markup=reply_markup
                        )
                    else:
                        try:
                            await update.callback_query.edit_message_caption(
                                caption=harem_message, 
                                reply_markup=reply_markup
                            )
                        except BadRequest:
                            await update.callback_query.edit_message_reply_markup(reply_markup=reply_markup)
                elif 'vid_url' in fav_character:
                    if update.message:
                        await update.message.reply_video(
                            video=fav_character['vid_url'], 
                            caption=harem_message, 
                            reply_markup=reply_markup,
                            supports_streaming=True
                        )
                    else:
                        try:
                            await update.callback_query.edit_message_caption(
                                caption=harem_message, 
                                reply_markup=reply_markup
                            )
                        except BadRequest:
                            await update.callback_query.edit_message_reply_markup(reply_markup=reply_markup)
            else:
                await _send_harem_message(update, harem_message, reply_markup)
        else:
            await _send_harem_message(update, harem_message, reply_markup, user['characters'])
    except Exception as e:
        print(f"Failed to edit message: {e}")



async def _send_harem_message(update, harem_message, reply_markup, characters=None):
    if characters:
        random_character = random.choice(characters)
        if 'img_url' in random_character:
            if update.message:
                await update.message.reply_photo(photo=random_character['img_url'], caption=harem_message, reply_markup=reply_markup)
            else:
                try:
                    await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup)
                except BadRequest:
                    await update.callback_query.edit_message_reply_markup(reply_markup=reply_markup)
        elif 'vid_url' in random_character:
            if update.message:
                await update.message.reply_video(video=random_character['vid_url'], caption=harem_message, reply_markup=reply_markup, supports_streaming=True)
            else:
                try:
                    await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup)
                except BadRequest:
                    await update.callback_query.edit_message_reply_markup(reply_markup=reply_markup)
        else:
            await _send_text_message(update, harem_message, reply_markup)
    else:
        await _send_text_message(update, harem_message, reply_markup)
        

    
async def _send_text_message(update, text, reply_markup):
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        try:
            await update.callback_query.edit_message_caption(caption=text, reply_markup=reply_markup)
        except BadRequest:
            await update.callback_query.edit_message_reply_markup(reply_markup=reply_markup)
            





async def get_user_rarity_mode(user_id: int) -> str:
    user = await user_collection.find_one({'id': user_id})
    return user.get('rarity_mode', 'All') if user else 'All'

async def update_user_rarity_mode(user_id: int, rarity_mode: str) -> None:
    await user_collection.update_one({'id': user_id}, {'$set': {'rarity_mode': rarity_mode}}, upsert=True)

def error(update: Update, context: CallbackContext):
    logging.error(f"Error: {context.error}")

async def pagination_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    print(f"Received callback query: {data}")
    page = int(data.split(':')[1])
    await harem(update, context, page)


application.add_handler(CommandHandler(["ncollection", "mycollection"], harem))
application.add_handler(CommandHandler("rmmmusers", remove_all_pm_users))

application.add_handler(CallbackQueryHandler(pagination_callback, pattern='^harem:'))
application.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.message.delete(), pattern='^close$'))
application.add_error_handler(error)

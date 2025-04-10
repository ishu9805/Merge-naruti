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

MAX_CAPTION_LENGTH = 1024

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext
from itertools import groupby
import math
import random
from html import escape
from telegram.error import BadRequest
import logging

# Define rarity emojis
RARITY_MAPPING = {
    '⚪️ Common': '⚪️',
    '🟣 Rare': '🟣',
    '🟡 Legendary': '🟡',
    '🟢 Medium': '🟢',
    '💮 Special Edition': '💮',
    '🔮 Limited Edition': '🔮',
    '💸 Premium Edition': '💸',
    '🌤 Summer': '🌤',
    '🎐 Celestial': '🎐',
    '❄️ Winter': '❄️',
    '💝 Valentine': '💝',
    '🎃 Halloween': '🎃',
    '🎄 Christmas Special': '🎄',
    '🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐': '🪐',
    '🎭 Cosplay Master 🎭': '🎭',
    '🎖 Apex Lot ( AUCTION )': '🎖',
    '🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣': '🎗️',
    '🧧 𝙀𝙫𝙚𝙣𝙩𝙨': '🧧'
}

# Define type emojis
TYPE_MAPPING = {
    '⚽': "Football",
    '🏀': "Basketball",
    '🎊': "Cheerleader",
    '🏖': "Summer",
    '☃️': "Winter",
    '❄️': "Winter",
    '🎃': "Halloween",
    '🎄': "Christmas",
    '🥻': "Saree",
    '🏴‍☠️': "Pirate",
    '👑': "Royalty",
    '🚨': "Officer",
    '👘': "Kimono",
    '👙': "Bikini",
    '🎒': "School",
    '🏜': "Egypt",
    '🎀': "Serena",
    '💍': "Wedding",
    '🩺': "Doctor",
    '💪': "GYM",
    '🧹': "Maid",
    '🐰': "Bunny",
    '💝': "Valentine",
    '🏐': "Volleyball",
    '🍷': "Drunk",
    '🎩': "Assembly",
    '🎨': "Coloured",
    '🚓': "Police",
    '💉': "Nurses",
    '🦠': "Toxic",
    '🎅': "Christmas",
    '🧧': "Chinese New Year",
    '🪽': "Angelic",
    '🍫': "Chocolates",
    '🔞': "+18",
    '🧬': "Cross-Verse",
    '👶': "Chibi",
    '🪙': "Treasure"
}

MAX_CAPTION_LENGTH = 1024

async def harem(update: Update, context: CallbackContext, page=0, filter_type=None, filter_value=None) -> None:
    user_id = update.effective_user.id
    user = await user_collection.find_one({'id': user_id})
    is_banned = await ban_collection.find_one({"user_id": user_id})
    
    if is_banned:
        return

    if not user or 'characters' not in user or not user['characters']:
        empty_messages = [
            "🌌 Your collection is empty...",
            "🕳️ Nothing here but darkness...",
            "🌫️ Your harem awaits its first shadow..."
        ]
        message = random.choice(empty_messages)
        if update.message:
            await update.message.reply_text(message)
        else:
            await update.callback_query.edit_message_text(message)
        return

    # Apply filters
    characters = user['characters']
    if filter_type == 'rarity':
        characters = [c for c in characters if c.get('rarity') == filter_value]
    elif filter_type == 'type':
        characters = [c for c in characters if filter_value in c.get('type', [])]

    # Sort and process characters
    characters = sorted(characters, key=lambda x: (x['anime'], x['id']))
    character_counts = {k: len(list(v)) for k, v in groupby(sorted(characters, key=lambda x: x['id']), key=lambda x: x['id'])}
    unique_characters = list({char['id']: char for char in characters}.values())
    total_count = len(characters)

    # Pagination
    chars_per_page = 15
    total_pages = math.ceil(len(unique_characters) / chars_per_page)
    page = max(0, min(page, total_pages-1))
    current_chars = unique_characters[page*chars_per_page:(page+1)*chars_per_page]

    # Build message
    harem_message = f"{escape(update.effective_user.first_name)}'s Harem - Page {page+1}/{total_pages}\n\n"
    
    # Add filter info if applied
    if filter_type:
        filter_emoji = RARITY_MAPPING.get(filter_value, "") if filter_type == "rarity" else \
                      next((k for k, v in TYPE_MAPPING.items() if v == filter_value), "")
        harem_message += f"🔮 Filter: {filter_emoji} {filter_value}\n\n"

    current_grouped_chars = {k: list(v) for k, v in groupby(current_chars, key=lambda x: x['anime'])}

    for anime, chars in current_grouped_chars.items():
        harem_message += f"⌬ {anime} 〔{len(chars)}〕\n"
        for char in chars:
            rarity = char['rarity']
            count = character_counts[char['id']]
            rarity_emoji = RARITY_MAPPING.get(rarity, '')
            type_emojis = " ".join([k for k, v in TYPE_MAPPING.items() if v in char.get('type', [])])
            harem_message += f"◈⌠{rarity_emoji}⌡ {type_emojis} {char['id']} {char['name']} (x{count})\n"
        harem_message += "\n"

    if len(harem_message) > MAX_CAPTION_LENGTH:
        harem_message = harem_message[:MAX_CAPTION_LENGTH]

    # Create buttons
    keyboard = []
    
    # Main buttons
    has_animated = any(char.get('rarity') == "🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣" and 'vid_url' in char for char in user['characters'])
    main_buttons = [
        InlineKeyboardButton(f"🦋 Static [{total_count}]", switch_inline_query_current_chat=f"collection.img.{user_id}"),
        InlineKeyboardButton("🎗️ 𝘼𝙈𝙑", switch_inline_query_current_chat=f"collection.vid.{user_id}") if has_animated else None
    ]
    keyboard.append([btn for btn in main_buttons if btn])

    # Filter buttons
    filter_buttons = [
        InlineKeyboardButton("🔮 By Rarity", callback_data=f"harem_filter:rarity:{page}"),
        InlineKeyboardButton("🎭 By Type", callback_data=f"harem_filter:type:{page}"),
        InlineKeyboardButton("🌀 Reset", callback_data=f"harem_filter:reset:{page}")
    ]
    keyboard.append(filter_buttons)

    # Pagination buttons
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"harem:{page-1}:{filter_type or ''}:{filter_value or ''}"))
        nav_buttons.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"harem:{page+1}:{filter_type or ''}:{filter_value or ''}"))
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton("Close", callback_data="close")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send message with media
    try:
        display_char = _get_display_character(user, filter_type, filter_value)
        if 'img_url' in display_char:
            if update.message:
                await update.message.reply_photo(
                    photo=display_char['img_url'], 
                    caption=harem_message, 
                    reply_markup=reply_markup
                )
            else:
                try:
                    await update.callback_query.edit_message_media(
                        InputMediaPhoto(display_char['img_url'], caption=harem_message),
                        reply_markup=reply_markup
                    )
                except BadRequest:
                    await update.callback_query.edit_message_caption(
                        caption=harem_message, 
                        reply_markup=reply_markup
                    )
        elif 'vid_url' in display_char:
            if update.message:
                await update.message.reply_video(
                    video=display_char['vid_url'], 
                    caption=harem_message, 
                    reply_markup=reply_markup,
                    supports_streaming=True
                )
            else:
                try:
                    await update.callback_query.edit_message_media(
                        InputMediaVideo(display_char['vid_url'], caption=harem_message),
                        reply_markup=reply_markup
                    )
                except BadRequest:
                    await update.callback_query.edit_message_caption(
                        caption=harem_message, 
                        reply_markup=reply_markup
                    )
        else:
            await _send_text_message(update, harem_message, reply_markup)
    except Exception as e:
        logging.error(f"Failed to edit message: {e}")
        await _send_text_message(update, harem_message, reply_markup)

def _get_display_character(user, filter_type=None, filter_value=None):
    """Select the best character to display based on filters and favorites"""
    characters = user['characters']
    
    # Apply filters if specified
    if filter_type == 'rarity':
        characters = [c for c in characters if c.get('rarity') == filter_value]
    elif filter_type == 'type':
        characters = [c for c in characters if filter_value in c.get('type', [])]
    
    # Try favorite first
    if 'favorites' in user and user['favorites']:
        fav_char = next((c for c in characters if c['id'] == user['favorites'][0]), None)
        if fav_char:
            return fav_char
    
    # Fallback to random character from filtered set
    return random.choice(characters) if characters else random.choice(user['characters'])

async def _send_text_message(update, text, reply_markup):
    """Fallback for text-only messages"""
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        try:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        except BadRequest:
            await update.callback_query.edit_message_reply_markup(reply_markup=reply_markup)

async def harem_callback(update: Update, context: CallbackContext):
    """Handle all harem-related callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "close":
        await query.message.delete()
        return
    elif query.data == "noop":
        return
    
    try:
        if query.data.startswith("harem_filter:"):
            parts = query.data.split(":")
            filter_type = parts[1]
            current_page = int(parts[2])
            
            if filter_type == "rarity":
                # Show rarity selection
                buttons = [
                    [InlineKeyboardButton(f"{emoji} {name}", callback_data=f"harem_filter_select:rarity:{name}:{current_page}")]
                    for name, emoji in RARITY_MAPPING.items()
                ]
                buttons.append([InlineKeyboardButton("🔙 Back", callback_data=f"harem:{current_page}")])
                await query.edit_message_reply_markup(InlineKeyboardMarkup(buttons))
            elif filter_type == "type":
                # Show type selection (grouped in 3 columns)
                types = sorted(TYPE_MAPPING.items(), key=lambda x: x[1])
                buttons = [
                    [
                        InlineKeyboardButton(f"{emoji} {name}", callback_data=f"harem_filter_select:type:{name}:{current_page}")
                        for emoji, name in types[i:i+3]
                    ]
                    for i in range(0, len(types), 3)
                ]
                buttons.append([InlineKeyboardButton("🔙 Back", callback_data=f"harem:{current_page}")])
                await query.edit_message_reply_markup(InlineKeyboardMarkup(buttons))
            elif filter_type == "reset":
                await harem(update, context, current_page)
                
        elif query.data.startswith("harem_filter_select:"):
            parts = query.data.split(":")
            filter_type = parts[1]
            filter_value = parts[2]
            current_page = int(parts[3])
            await harem(update, context, current_page, filter_type, filter_value)
            
        else:  # Regular pagination
            parts = query.data.split(":")
            page = int(parts[1])
            filter_type = parts[2] if len(parts) > 2 and parts[2] else None
            filter_value = parts[3] if len(parts) > 3 and parts[3] else None
            await harem(update, context, page, filter_type, filter_value)
            
    except Exception as e:
        logging.error(f"Harem callback error: {e}")
        await query.answer("Error processing request, please try again.")

# Register handlers
application.add_handler(CommandHandler(["ncollection", "mycollection", "harem"], harem))
application.add_handler(CallbackQueryHandler(harem_callback, pattern='^harem'))
application.add_handler(CallbackQueryHandler(harem_callback, pattern='^harem_filter'))
application.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.message.delete(), pattern='^close$'))

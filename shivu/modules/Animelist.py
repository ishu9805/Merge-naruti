from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict
import string
from shivu import collectionps as collection, shivuups as app

# Global dictionary to store current page positions
user_page_positions = {}

async def get_anime_by_letter(letter: str) -> List[str]:
    """Get distinct anime names starting with a specific letter"""
    regex_pattern = f'^{letter}'  # Case-sensitive regex
    pipeline = [
        {"$match": {"anime": {"$regex": regex_pattern}}},
        {"$group": {"_id": "$anime"}},
        {"$sort": {"_id": 1}}
    ]
    anime_list = await collection.aggregate(pipeline).to_list(length=None)
    return [anime['_id'] for anime in anime_list]

async def get_characters_by_anime(anime_name: str) -> List[Dict]:
    """Get all characters from a specific anime"""
    return await collection.find({"anime": anime_name}).to_list(length=None)

@app.on_message(filters.command("animelist"))
async def animelist_command(client, message):
    """Show A-Z buttons for anime selection with pagination"""
    # Create two rows of A-Z buttons (13 letters each)
    letters = list(string.ascii_uppercase)
    row1 = letters[:13]  # A-M
    row2 = letters[13:]  # N-Z
    
    buttons = []
    buttons.append([InlineKeyboardButton(letter, callback_data=f"animelist_{letter}_0") for letter in row1])
    buttons.append([InlineKeyboardButton(letter, callback_data=f"animelist_{letter}_0") for letter in row2])
    
    await message.reply_text(
        "**Select an anime by first letter:**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_callback_query(filters.regex(r"^animelist_([A-Z])_(\d+)$"))
async def anime_letter_callback(client, callback_query):
    """Handle letter selection with pagination"""
    letter = callback_query.matches[0].group(1)
    page = int(callback_query.matches[0].group(2))
    
    anime_list = await get_anime_by_letter(letter)
    if not anime_list:
        await callback_query.answer("No anime found starting with this letter!", show_alert=True)
        return
    
    # Store the current anime list for this user
    user_page_positions[callback_query.from_user.id] = {
        'letter': letter,
        'anime_list': anime_list,
        'page': page
    }
    
    # Create buttons for current page (5 per page)
    buttons = []
    start_idx = page * 5
    end_idx = min(start_idx + 5, len(anime_list))
    
    for anime in anime_list[start_idx:end_idx]:
        inline_query = f"{anime}"
        buttons.append([InlineKeyboardButton(
            anime,
            callback_data=f"anime_select_{anime}",
        )])
    
    # Add navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            "⬅️ Previous", 
            callback_data=f"animelist_{letter}_{page-1}"
        ))
    if end_idx < len(anime_list):
        nav_buttons.append(InlineKeyboardButton(
            "Next ➡️", 
            callback_data=f"animelist_{letter}_{page+1}"
        ))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(
        "🔙 Back to A-Z", 
        callback_data="back_to_az"
    )])
    
    await callback_query.message.edit_text(
        f"**Anime starting with '{letter}' (Page {page+1}):**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^anime_select_(.+)$"))
async def anime_selection_callback(client, callback_query):
    """Handle anime selection"""
    anime_name = callback_query.matches[0].group(1)
    
    # Create inline search button
    inline_query = f"{anime_name}"
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(
            "🔍 Search Characters", 
            switch_inline_query_current_chat=inline_query
        )]]
    )
    
    await callback_query.message.reply_text(
        f"**Selected Anime:** {anime_name}\n\n"
        "Click the button below to search characters from this anime:",
        reply_markup=keyboard
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^back_to_az$"))
async def back_to_az_callback(client, callback_query):
    """Return to A-Z selection"""
    # Create two rows of A-Z buttons (13 letters each)
    letters = list(string.ascii_uppercase)
    row1 = letters[:13]  # A-M
    row2 = letters[13:]  # N-Z
    
    buttons = []
    buttons.append([InlineKeyboardButton(letter, callback_data=f"animelist_{letter}_0") for letter in row1])
    buttons.append([InlineKeyboardButton(letter, callback_data=f"animelist_{letter}_0") for letter in row2])
    
    await callback_query.message.edit_text(
        "**Select an anime by first letter:**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await callback_query.answer()

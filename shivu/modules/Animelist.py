from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict
import string
from shivu import collectionps as collection, shivuups as app

# Global dictionary to store current page positions
user_page_positions = {}



# Dictionary to track users who used the command
active_users = {}

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

@app.on_message(filters.command("animelist"))
async def animelist_command(client, message):
    """Show A-Z buttons for anime selection in 3 rows"""
    user_id = message.from_user.id
    active_users[user_id] = True  # Mark user as active
    
    # Split A-Z into 3 rows (9, 9, 8 letters)
    letters = list(string.ascii_uppercase)
    row1 = letters[:9]   # A-I
    row2 = letters[9:18] # J-R
    row3 = letters[18:]  # S-Z
    
    buttons = [
        [InlineKeyboardButton(letter, callback_data=f"animelist_{letter}_0") for letter in row1],
        [InlineKeyboardButton(letter, callback_data=f"animelist_{letter}_0") for letter in row2],
        [InlineKeyboardButton(letter, callback_data=f"animelist_{letter}_0") for letter in row3]
    ]
    
    await message.reply_text(
        "**Select an anime by first letter:**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_callback_query(filters.regex(r"^animelist_([A-Z])_(\d+)$"))
async def anime_letter_callback(client, callback_query):
    """Handle letter selection with pagination"""
    user_id = callback_query.from_user.id
    if user_id not in active_users:
        await callback_query.answer("Please use /animelist command first!", show_alert=True)
        return
    
    letter = callback_query.matches[0].group(1)
    page = int(callback_query.matches[0].group(2))
    
    anime_list = await get_anime_by_letter(letter)
    if not anime_list:
        await callback_query.answer("No anime found starting with this letter!", show_alert=True)
        return
    
    # Create buttons for current page (5 per page)
    buttons = []
    start_idx = page * 5
    end_idx = min(start_idx + 5, len(anime_list))
    
    for anime in anime_list[start_idx:end_idx]:
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
    user_id = callback_query.from_user.id
    if user_id not in active_users:
        await callback_query.answer("Please use /animelist command first!", show_alert=True)
        return
    
    anime_name = callback_query.matches[0].group(1)
    
    # Create inline search button
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(
            "🔍 Search Characters", 
            switch_inline_query_current_chat=anime_name
        )]]
    )
    
    await callback_query.message.reply_text(
        f"**Selected Anime:** {anime_name}\n\n"
        "Click below to search characters from this anime:",
        reply_markup=keyboard
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^back_to_az$"))
async def back_to_az_callback(client, callback_query):
    """Return to A-Z selection"""
    user_id = callback_query.from_user.id
    if user_id not in active_users:
        await callback_query.answer("Please use /animelist command first!", show_alert=True)
        return
    
    # Split A-Z into 3 rows (9, 9, 8 letters)
    letters = list(string.ascii_uppercase)
    row1 = letters[:9]   # A-I
    row2 = letters[9:18] # J-R
    row3 = letters[18:]  # S-Z
    
    buttons = [
        [InlineKeyboardButton(letter, callback_data=f"animelist_{letter}_0") for letter in row1],
        [InlineKeyboardButton(letter, callback_data=f"animelist_{letter}_0") for letter in row2],
        [InlineKeyboardButton(letter, callback_data=f"animelist_{letter}_0") for letter in row3]
    ]
    
    await callback_query.message.edit_text(
        "**Select an anime by first letter:**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await callback_query.answer()

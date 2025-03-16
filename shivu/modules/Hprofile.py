import math
import os
import aiohttp
import aiofiles
from pyrogram import Client, filters
from datetime import datetime
import pytz
import asyncio
from . import user_collection, collection, app, chat_data
from .block import block_dec, temp_block

def custom_format_number(num):
    if int(num) >= 10**6:
        exponent = int(math.log10(num)) - 5
        base = num // (10 ** exponent)
        return f"{base:,.0f}({exponent:+})"
    return f"{num:,.0f}"

def parse_amount(amount_str):
    if "+" in amount_str:
        base_str, exponent_str = amount_str.split("+")
        base = int(base_str.replace(",", ""))
        exponent = int(exponent_str)
        return base * (10 ** exponent)
    return int(amount_str.replace(",", ""))

async def download_image(url, file_path):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(await response.read())

def calculate_days_old(created_at):
    now = datetime.now(pytz.timezone('Asia/Kolkata'))
    days_old = (now - created_at).days
    return days_old

def create_progress_bar(percentage, bar_length=10):
    """
    Create a progress bar using Unicode block elements.
    :param percentage: The percentage of progress (0 to 100).
    :param bar_length: The length of the progress bar (default: 10).
    :return: A string representing the progress bar.
    """
    filled_length = int(round(bar_length * percentage / 100))
    empty_length = bar_length - filled_length
    return '█' * filled_length + '░' * empty_length

async def update_chat_data(chat_id, user_id, characters_collected):
    """
    Update the total_characters for a user in a specific chat.
    """
    await chat_data.update_one(
        {'chat_id': chat_id, 'user_id': user_id},
        {'$inc': {'total_characters': characters_collected}, '$set': {'last_updated': datetime.now()}},
        upsert=True  # Create a new document if it doesn't exist
    )

async def get_chat_rank(chat_id, user_id):
    """
    Get the user's rank in the chat based on total_characters.
    """
    # Fetch all users in the chat sorted by total_characters in descending order
    chat_users = await chat_data.find({'chat_id': chat_id}).sort('total_characters', -1).to_list(None)

    # Find the user's rank
    for index, user in enumerate(chat_users):
        if user['user_id'] == user_id:
            return index + 1  # Rank is 1-based

    return None  # User not found in the chat data

async def upgrade_chat_data():
    """
    Upgrade the chat_data collection by adding all users to their respective chat groups.
    """
    # Fetch all users from user_collection
    users = await user_collection.find({}).to_list(None)

    # Fetch all chat groups where the bot is a member
    async for dialog in app.get_dialogs():
        if dialog.chat.type in ["group", "supergroup"]:
            chat_id = dialog.chat.id

            # Update chat_data for each user in the chat
            for user in users:
                user_id = user['id']
                total_characters = user.get('total_characters', 0)

                # Update or insert the user's data in chat_data
                await chat_data.update_one(
                    {'chat_id': chat_id, 'user_id': user_id},
                    {'$set': {'total_characters': total_characters, 'last_updated': datetime.now()}},
                    upsert=True  # Create a new document if it doesn't exist
                )

    print("✅ chat_data collection upgraded successfully!")

@app.on_start()
async def on_start(client):
    """
    Run the chat_data upgrade process when the bot starts.
    """
    print("🚀 Bot is starting...")
    await upgrade_chat_data()

@app.on_message(filters.command('hprofile'))
@block_dec
async def xprofile(client, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    try:
        # Send loading animation
        loading_message = await message.reply_text("⏳ Loading your profile...")

        # Simulate a 3-second delay
        await asyncio.sleep(3)

        # Fetch user data
        user_data = await user_collection.find_one(
            {'id': user_id},
            projection={'coins': 1, 'tokens': 1, 'total_characters': 1, 'gender': 1, 'profile_media': 1, 'created_at': 1}
        )

        if user_data:
            coins = int(user_data.get('coins', 0))
            tokens = int(user_data.get('tokens', 0))
            characters = user_data.get('total_characters', 0)
            gender = user_data.get('gender')
            profile_media = user_data.get('profile_media')
            created_at = user_data.get('created_at')

            if created_at:
                created_at = created_at.replace(tzinfo=pytz.timezone('Asia/Kolkata'))
                days_old = calculate_days_old(created_at)
            else:
                days_old = "N/A"

            total_characters = characters
            all_characters = await collection.count_documents({})
            total_database_characters = all_characters

            # Calculate progress bar percentage
            if total_database_characters > 0:
                progress_percentage = (total_characters / total_database_characters) * 100
                progress_bar = create_progress_bar(progress_percentage)
            else:
                progress_percentage = 0
                progress_bar = create_progress_bar(0)

            gender_icon = '👦🏻' if gender == 'male' else '👧🏻' if gender == 'female' else '👶🏻'

            # Fetch chat-specific data
            chat_id = message.chat.id
            chat_user_rank = await get_chat_rank(chat_id, user_id)
            chat_members_count = await chat_data.count_documents({'chat_id': chat_id})

            # Calculate user's global rank
            global_user_rank = await user_collection.count_documents({
                'total_characters': {'$gt': characters}
            }) + 1

            # Total users in the bot
            total_users = await user_collection.count_documents({})

            # Build the profile message with Markdown formatting
            balance_message = (
                f"🌟 **Profile** 🌟\n\n"
                f"👤 **Name**: {message.from_user.first_name or ''} {message.from_user.last_name or ''} [{gender_icon}]\n"
                f"🆔 **ID**: `{user_id}`\n\n"
                f"💰 **Coins**: `Ŧ{custom_format_number(coins)}`\n"
                f"🎟️ **Tokens**: `Ŧ{custom_format_number(tokens)}`\n"
                f"📜 **Characters**: `{total_characters}/{total_database_characters}`\n"
                f"📊 **Progress**: `{progress_bar}` `{progress_percentage:.2f}%`\n"
                f"📅 **Days Old**: `{days_old}`\n\n"
                f"🏆 **Chat Group Rank**: `#{chat_user_rank}` / `{chat_members_count}` members\n"
                f"🌍 **Global Rank**: `#{global_user_rank}` / `{total_users}` users\n"
            )

            # Send profile picture if available
            if profile_media:
                await message.reply_photo(
                    photo=profile_media,
                    caption=balance_message,
                    parse_mode="markdown"  # Enable Markdown formatting
                )
            else:
                await message.reply_text(
                    balance_message,
                    parse_mode="markdown"  # Enable Markdown formatting
                )

        else:
            await message.reply_text("Start the bot in DM first: [Fancy Waifu Husbando Bot](https://t.me/Fancy_Waifu_Husbando_Bot?start=start)")

        # Delete the loading message
        await loading_message.delete()

    except Exception as e:
        await message.reply_text(f"❌ An error occurred: {e}")


import math
import os
import aiohttp
import aiofiles
from pyrogram import Client, filters
from datetime import datetime
import pytz
from . import user_collection, collection, app
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

@app.on_message(filters.command('hprofile'))
@block_dec
async def xprofile(client, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    try:
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

            # Calculate user's rank in the chat group
            chat_id = message.chat.id
            chat_members = await app.get_chat_members_count(chat_id)
            chat_user_rank = await user_collection.count_documents({
                'chat_id': chat_id,
                'total_characters': {'$gt': characters}
            }) + 1

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
                f"🏆 **Chat Group Rank**: `#{chat_user_rank}` / `{chat_members}` members\n"
                f"🌍 **Global Rank**: `#{global_user_rank}` / `{total_users}` users\n"
            )

            # Send profile picture if available
            if profile_media:
                temp_file_path = "temp_profile_image.jpg"
                await download_image(profile_media, temp_file_path)

                await message.reply_photo(
                    photo=temp_file_path,
                    caption=balance_message,
                    parse_mode="markdown"  # Enable Markdown formatting
                )

                os.remove(temp_file_path)
            else:
                await message.reply_text(
                    balance_message,
                    parse_mode="markdown"  # Enable Markdown formatting
                )

        else:
            await message.reply_text("🚫 Claim your bonus first using /xbonus")

    except Exception as e:
        await message.reply_text(f"❌ An error occurred: {e}")

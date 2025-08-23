from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from shivu import applicationps as application, collectionps as collection
from pymongo.errors import PyMongoError

from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from shivu import applicationps as application, collectionps as collection
from pymongo.errors import PyMongoError

# Configuration
CHANNEL_ID = -1002519377646  # Your channel ID
OWNER_ID = 6902029663  # Your Telegram user ID
DELAY_BETWEEN_MESSAGES = 3  # Seconds between sends

async def send_all_characters(update: Update, context: CallbackContext):
    """Command handler to send ALL characters to channel in numerical ID order with optional start ID"""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 You are not authorized to use this command.")
        return

    try:
        # Check if a starting ID was provided
        start_id = None
        if context.args:
            try:
                start_id = int(context.args[0])
            except ValueError:
                await update.message.reply_text("❌ Please provide a valid numeric starting ID.")
                return

        # Count ALL characters regardless of sent status
        total_characters = await collection.count_documents({})
        if total_characters == 0:
            await update.message.reply_text("❌ No characters found in database!")
            return

        progress_msg = await update.message.reply_text(
            f"⏳ Preparing to send ALL {total_characters} characters in numerical order..."
            + (f"\n🚩 Starting from ID: {start_id}" if start_id is not None else "")
        )
        
        successfully_sent = 0
        failed_to_send = 0
        skipped_before_start = 0
        
        # Get ALL characters and sort them numerically by ID
        all_chars = []
        async for char in collection.find({}):
            all_chars.append(char)
        
        # Sort numerically by ID (convert to int for proper numeric sorting)
        all_chars.sort(key=lambda x: int(x.get('id', 0)))
        
        for character in all_chars:
            current_id = int(character.get('id', 0))
            
            # Skip characters before the starting ID if specified
            if start_id is not None and current_id < start_id:
                skipped_before_start += 1
                continue
                
            try:
                # Send the character (regardless of previous sent status)
                await send_character_to_channel(context.bot, character)
                
                # Update sent status (optional - remove if you don't want to track)
                await collection.update_one(
                    {"_id": character["_id"]},
                    {"$set": {"sented": True}}
                )
                
                successfully_sent += 1
                
                # Update progress every 10 characters
                if successfully_sent % 10 == 0:
                    await progress_msg.edit_text(
                        f"⏳ Progress: {successfully_sent}/{total_characters}\n"
                        f"📌 Current ID: {character.get('id', 'N/A')}\n"
                        f"✅ Sent: {successfully_sent}\n"
                        f"❌ Failed: {failed_to_send}\n"
                        f"⏭ Skipped: {skipped_before_start}"
                    )
                
                await asyncio.sleep(DELAY_BETWEEN_MESSAGES)
            
            except Exception as e:
                print(f"Failed to send character {character.get('id')}: {str(e)}")
                failed_to_send += 1
                continue
        
        # Final report
        await progress_msg.edit_text(
            f"🎉 Completed Sending Characters!\n\n"
            f"📊 Results:\n"
            f"✅ Successfully sent: {successfully_sent}\n"
            f"❌ Failed to send: {failed_to_send}\n"
            f"⏭ Skipped before start ID: {skipped_before_start}\n"
            f"📦 Total in database: {total_characters}\n"
            f"🆔 Highest ID sent: {character.get('id', 'N/A')}"
        )
    
    except PyMongoError as e:
        await update.message.reply_text(f"❌ Database error: {str(e)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Unexpected error: {str(e)}")

async def send_character_to_channel(bot, character_data):
    """Send a single character to channel with formatted message"""
    char_id = character_data.get('id', 'N/A')
    
    caption = (
        f"🆔 ID: {char_id}\n"
        f"📛 Name: {character_data.get('name', 'Unknown')}\n"
        f"🎌 Anime: {character_data.get('anime', 'Unknown')}\n"
        f"🌟 Rarity: {character_data.get('rarity', 'Unknown')}\n"
    )
    
    if 'img_url' in character_data:
        await bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=character_data['img_url'],
            caption=caption
        )
    elif 'vid_url' in character_data:
        await bot.send_video(
            chat_id=CHANNEL_ID,
            video=character_data['vid_url'],
            caption=caption,
            supports_streaming=True
        )
    else:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"📄 Character Data\n\n{caption}"
        )



from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from telegram.error import TelegramError
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from . import sudo_filter
from shivu import applicationps as application, collectionps as collection
from pymongo.errors import PyMongoError

# Configuration
CHANNEL_ID = -1002519377646  # Your channel ID
OWNER_ID = 6902029663  # Your Telegram user ID

async def send_one_character(update: Update, context: CallbackContext):
    """Command handler to send a single character to channel by ID"""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 You are not authorized to use this command.")
        return

    # Check if a character ID was provided
    if not context.args:
        await update.message.reply_text("❌ Please provide a character ID.\nUsage: /sendone <character_id>")
        return

    try:
        character_id = context.args[0]
        
        # Find the character by ID
        character = await collection.find_one({"id": character_id})
        
        if not character:
            await update.message.reply_text(f"❌ Character with ID {character_id} not found in database!")
            return

        # Send the character to channel
        try:
            await send_character_to_channel(context.bot, character)
            
            # Update sent status
            await collection.update_one(
                {"_id": character["_id"]},
                {"$set": {"sented": True}}
            )
            
            await update.message.reply_text(f"✅ Successfully sent character {character_id} to channel!")
            
        except TelegramError as e:
            await update.message.reply_text(f"❌ Failed to send character to channel: {str(e)}")
            
    except PyMongoError as e:
        await update.message.reply_text(f"❌ Database error: {str(e)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Unexpected error: {str(e)}")

async def send_character_to_channel(bot, character_data):
    """Send a single character to channel with formatted message"""
    char_id = character_data.get('id', 'N/A')
    
    caption = (
        f"🆔 ID: {char_id}\n"
        f"📛 Name: {character_data.get('name', 'Unknown')}\n"
        f"🎌 Anime: {character_data.get('anime', 'Unknown')}\n"
        f"🌟 Rarity: {character_data.get('rarity', 'Unknown')}\n"
    )
    
    try:
        if 'img_url' in character_data:
            await bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=character_data['img_url'],
                caption=caption
            )
        elif 'vid_url' in character_data:
            await bot.send_video(
                chat_id=CHANNEL_ID,
                video=character_data['vid_url'],
                caption=caption,
                supports_streaming=True
            )
        else:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"📄 Character Data\n\n{caption}"
            )
    except TelegramError as e:
        print(f"Telegram API error when sending character {char_id}: {str(e)}")
        raise

# Add handler
application.add_handler(CommandHandler("sendone", send_one_character))
# Add handler with a more descriptive command name
application.add_handler(CommandHandler("sendall", send_all_characters))

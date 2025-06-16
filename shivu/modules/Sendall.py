from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from shivu import applicationps as application, collectionps as collection
from pymongo.errors import PyMongoError

# Configuration
#TOKEN = "7880519589:AAGzxUrbOgJlHlv3JM7j_Jccj4sXZblmjZs"
#MONGO_URL = "mongodb+srv://babusona:hinatababy@cluster0.t0lfelh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
CHANNEL_ID = -1002519377646 # Replace with your channel ID
OWNER_ID = 6902029663  # Your Telegram user ID
DELAY_BETWEEN_MESSAGES = 3  # Seconds between sends

# Initialize MongoDB connection

async def sendall(update: Update, context: CallbackContext):
    """Command handler to send all unsent characters to channel"""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 You are not authorized to use this command.")
        return

    try:
        # Count only unsent characters
        total = await collection.count_documents({"sented": {"$ne": True}})
        if total == 0:
            await update.message.reply_text("✅ All characters have already been sent!")
            return

        progress_msg = await update.message.reply_text(f"⏳ Starting to send {total} unsent characters...")
        
        sent_count = 0
        failed_count = 0
        
        # Process only unsent characters
        async for character in collection.find({"sented": {"$ne": True}}):
            try:
                # Send the character
                await send_character(context.bot, character)
                
                # Mark as sent in database
                await collection.update_one(
                    {"_id": character["_id"]},
                    {"$set": {"sented": True}}
                )
                
                sent_count += 1
                
                # Update progress every 10 characters
                if sent_count % 10 == 0:
                    await progress_msg.edit_text(
                        f"⏳ Progress: {sent_count}/{total} sent\n"
                        f"✅ Success: {sent_count}\n"
                        f"❌ Failed: {failed_count}"
                    )
                
                await asyncio.sleep(DELAY_BETWEEN_MESSAGES)
            
            except Exception as e:
                print(f"Failed to send character {character.get('id')}: {str(e)}")
                failed_count += 1
                continue
        
        # Final report
        await progress_msg.edit_text(
            f"📊 Send All Complete!\n\n"
            f"✅ Successfully sent: {sent_count}\n"
            f"❌ Failed to send: {failed_count}\n"
            f"📦 Total unsent processed: {total}"
        )
    
    except PyMongoError as e:
        await update.message.reply_text(f"❌ Database error: {str(e)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Unexpected error: {str(e)}")

async def send_character(bot, character):
    """Send a single character to channel"""
    caption = (
        f"🆔 ID: {character.get('id', 'N/A')}\n"
        f"📛 Name: {character.get('name', 'Unknown')}\n"
        f"🎌 Anime: {character.get('anime', 'Unknown')}\n"
        f"🌟 Rarity: {character.get('rarity', 'Unknown')}\n"
    )
    
    if 'img_url' in character:
        await bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=character['img_url'],
            caption=caption
        )
    elif 'vid_url' in character:
        await bot.send_video(
            chat_id=CHANNEL_ID,
            video=character['vid_url'],
            caption=caption,
            supports_streaming=True
        )
    else:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"📄 Character Data\n\n{caption}"
        )


  
    # Add handler
application.add_handler(CommandHandler("sendall", sendall))
    

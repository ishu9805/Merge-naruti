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
CHANNEL_ID = -1002519377646  # Replace with your channel ID
OWNER_ID = 6902029663  # Your Telegram user ID
DELAY_BETWEEN_MESSAGES = 3  # Seconds between sends


async def sendall(update: Update, context: CallbackContext):
    """Command handler to send all unsent characters to channel in numerical ID order"""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 You are not authorized to use this command.")
        return

    try:
        # Count only unsent characters (where done is not True)
        total = await collection.count_documents({"dones": {"$ne": True}})
        if total == 0:
            await update.message.reply_text("✅ All characters have already been sent!")
            return

        progress_msg = await update.message.reply_text(
            f"⏳ Starting to send {total} unsent characters in numerical ID order..."
        )
        
        sent_count = 0
        failed_count = 0
        
        # Get all unsent characters and sort them numerically by ID
        all_characters = []
        async for character in collection.find({"dones": {"$ne": True}}):
            all_characters.append(character)
        
        # Sort numerically by ID (convert to int for proper numeric sorting)
        all_characters.sort(key=lambda x: int(x.get('id', 0)))
        
        for character in all_characters:
            try:
                # Send the character
                await send_character(context.bot, character)
                
                # Mark as done in database
                await collection.update_one(
                    {"_id": character["_id"]},
                    {"$set": {"dones": True, "sented": True}}
                )
                
                sent_count += 1
                
                # Update progress every 10 characters
                if sent_count % 10 == 0:
                    await progress_msg.edit_text(
                        f"⏳ Progress: {sent_count}/{total} sent\n"
                        f"📈 Current ID: {character.get('id', 'N/A')}\n"
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
            f"🎉 Send All Complete!\n\n"
            f"📊 Statistics:\n"
            f"✅ Successfully sent: {sent_count}\n"
            f"❌ Failed to send: {failed_count}\n"
            f"📦 Total processed: {total}\n"
            f"🆔 Highest ID sent: {character.get('id', 'N/A')}"
        )
    
    except PyMongoError as e:
        await update.message.reply_text(f"❌ Database error: {str(e)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Unexpected error: {str(e)}")

# Add handler
application.add_handler(CommandHandler("sendall", sendall))

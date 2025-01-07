from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
import asyncio
from shivu import user_collection, user_count
# Replace with your MongoDB connection and collection details
from shivu import shivuu as app
# Define a command to start counting characters
async def ucount_all(client: Client, message: Message):
    # Replace with your admin user ID
    ADMIN_IDS = [7378476666]

    # Check if the user is an admin
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("You are not authorized to use this command.")
        return

    processed_users = 0
    progress_threshold = 50  # Send a progress update every 50 users

    # Fetch all users from the user collection
    cursor = user_collection.find({})

    # Track the last processed user ID to continue from where it left off
    last_processed_user_id = None
    try:
        async for user in cursor:
            user_id = user.get('id')
            if not user_id:
                continue  # Skip invalid user entries

            # Count the number of characters the user has
            total_characters = len(user.get('characters', []))

            # Prepare the document for updating the user_count collection
            document = {
                'user_id': user_id,
                'ccount': total_characters
            }

            # Update or insert the user's character count
            await user_count.update_one(
                {'user_id': user_id},
                {'$set': document},
                upsert=True
            )

            # Increment processed user count
            processed_users += 1

            # Send progress updates every 'progress_threshold' users
            if processed_users % progress_threshold == 0:
                await message.reply(f"Processed {processed_users} users so far...")

            # Keep track of the last processed user ID
            last_processed_user_id = user_id

            # Simulate a small delay to avoid spamming updates
            await asyncio.sleep(1)

        # Final summary after all users are processed
        await message.reply(f"Finished processing {processed_users} users.")

    except Exception as e:
        # Handle errors and resume processing from the last user
        await message.reply(f"An error occurred: {e}")
        print(f"Error: {e}")

        # Resume from the last processed user in future executions
        if last_processed_user_id:
            await message.reply(f"Resuming from user ID {last_processed_user_id}.")

# Add the command handler
@app.on_message(filters.command("ull"))
async def handle_ucount_all(client, message):
    await ucount_all(client, message)



from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import user_count, application

async def count_user_documents(update: Update, context: CallbackContext):
    # Count the number of documents in the user_count collection
    count = await user_count.count_documents({})

    # Send the count as a reply
    await update.message.reply_text(f"There are {count} documents in the user_count collection.")

# Add the command handler
application.add_handler(CommandHandler("countusers", count_user_documents))

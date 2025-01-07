from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
import asyncio
from shivu import user_collection, user_count
# Replace with your MongoDB connection and collection details
from shivu import shivuu as app
# Define a command to start counting characters
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
import asyncio

            # Simulate a small delay to avoid spamming updates
            
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
import asyncio


# Define a function to process users in batches
async def ucount_all(client: Client, message: Message):
    # Replace with your admin user ID
    ADMIN_IDS = [7378476666]

    # Check if the user is an admin
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("You are not authorized to use this command.")
        return

    # Initialize counters
    processed_users = 0
    progress_threshold = 50  # Send a progress update every 50 users
    batch_size = 100  # Number of users to process per batch

    # Fetch the total number of users
    total_users = await user_collection.count_documents({})

    # Process users in batches
    for skip in range(0, total_users, batch_size):
        # Fetch the next batch of users
        users_batch = user_collection.find().skip(skip).limit(batch_size)

        # Convert the cursor to a list to allow iteration
        users = await users_batch.to_list(length=batch_size)

        # If there are no users in the batch, break the loop
        if not users:
            break

        # Iterate through each user in the current batch
        for user in users:
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

            # Simulate a small delay to avoid spamming updates
            await asyncio.sleep(1)

    # Final summary after all users are processed
    await message.reply(f"Finished processing {processed_users} users.")

# Add the command handler
@app.on_message(filters.command("userk"))
async def handle_ucount_all(client, message):
    await ucount_all(client, message)

# 




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

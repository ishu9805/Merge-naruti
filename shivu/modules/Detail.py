from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import user_collection, user_count, application
import asyncio

async def ucount_all(update: Update, context: CallbackContext):
    # Replace YOUR_ADMIN_ID with your Telegram user ID or list of admin IDs
    ADMIN_IDS = [7378476666]

    # Restrict the command to admins
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    # Initialize counters
    processed_users = 0
    progress_threshold = 500  # Update progress every 500 users
    batch_size = 100  # Batch size for fetching users
    skip = 0  # Initialize skip variable

    # Fetch users in batches
    while True:
        cursor = user_collection.find({}).skip(skip).limit(batch_size)

        batch_processed = 0
        async for user in cursor:
            user_id = user.get('id')
            if not user_id:
                continue  # Skip entries without a valid user ID

            # Check if the user is already processed (exists in user_count collection)
            existing_user = await user_count.find_one({'user_id': user_id})
            if existing_user:
                continue  # Skip if user has already been processed

            # Count the number of characters the user has
            total_characters = len(user.get('characters', []))

            # Prepare the new document for insertion
            document = {
                'user_id': user_id,
                'ccount': total_characters
            }

            # Update or insert the user's character count in user_count
            await user_count.update_one(
                {'user_id': user_id},  # Match user by ID
                {'$set': document},    # Insert or update with this document
                upsert=True            # Create new document if not present
            )

            processed_users += 1
            batch_processed += 1

            # Provide progress update for every 500 users processed
            if processed_users % progress_threshold == 0:
                await update.message.reply_text(f"Processed {processed_users} users so far...")

        # If no more users are left to process, exit the loop
        if batch_processed < batch_size:
            break

        skip += batch_size  # Move to the next batch

        # Throttle progress updates to avoid flooding the chat with messages
        await asyncio.sleep(1)

    # Final summary message
    await update.message.reply_text(f"Finished processing {processed_users} users.")

# Add the command handler
application.add_handler(CommandHandler("ull", ucount_all))





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

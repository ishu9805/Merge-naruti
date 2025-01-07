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
    progress_threshold = 50  # Set threshold for progress updates

    # Fetch all users from user_collection
    cursor = user_collection.find({})

    try:
        async for user in cursor:
            user_id = user.get('id')
            if not user_id:
                continue  # Skip entries without a valid user ID

            # Count the number of characters the user has
            total_characters = len(user.get('characters', []))

            # Prepare the new document for insertion if it doesn't exist
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

            # Provide progress update for every 50 users processed
            if processed_users % progress_threshold == 0:
                await update.message.reply_text(f"Processed {processed_users} users so far...")

            # Throttle progress updates to avoid flooding the chat with messages
            await asyncio.sleep(1)  # Add delay to prevent spamming updates

        # Final summary message
        await update.message.reply_text(f"Finished processing {processed_users} users.")

    except Exception as e:
        # Handle any errors during the process
        await update.message.reply_text(f"An error occurred: {e}")
        print(f"Error: {e}")

# Add the command handler
application.add_handler(CommandHandler("ull", ucount_all))

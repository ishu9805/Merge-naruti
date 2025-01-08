from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import user_collection, user_count, application 

# Admin IDs for restricted access
ADMIN_IDS = [7378476666]  # Replace with actual admin user IDs

async def ucount_all(update: Update, context: CallbackContext):
    # Restrict the command to admins
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    # Initialize counters
    processed_users = 0
    skipped_users = 0
    batch_size = 100  # Process in batches for better performance

    try:
        # Fetch all users from user_collection
        cursor = user_collection.find({'id': {'$exists': True, '$ne': None}})
        print("Processing started...")
        
        async for user in cursor:
            # Directly use user['id'] as 'id' is guaranteed to exist and be non-null
            user_id = user['id']

            # Check if the user_id is already present in user_count
            user_exists = await user_count.find_one({'user_id': user_id})
            if user_exists:
                skipped_users += 1
                continue  # Skip users already in user_count

            # Count the number of characters the user has
            total_characters = len(user.get('characters', []))

            # Prepare the new document for insertion or update
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
            print({processed_users})
            
            # Provide progress updates every batch_size users
            if processed_users % batch_size == 0:
                await update.message.reply_text(f"Processed {processed_users} users so far...")

        # Final summary message
        await update.message.reply_text(
            f"Finished processing {processed_users} users. Skipped {skipped_users} users already in user_count."
        )
    except Exception as e:
        # Log error and inform the user
        await update.message.reply_text(f"An error occurred: {e}")

# Add the command handler to the application
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


from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import user_count

async def top_users(update: Update, context: CallbackContext):
    """
    Fetch and display the top 10 users with the highest ccount.
    """
    try:
        # Fetch the top 10 users sorted by ccount in descending order
        top_users = await user_count.find({}).sort('ccount', -1).limit(10).to_list(length=10)

        if not top_users:
            await update.message.reply_text("No users found in the database.")
            return

        # Create a response message with the top users
        response = "🏆 Top 10 Users with Highest ccount 🏆\n\n"
        for rank, user in enumerate(top_users, start=1):
            user_id = user.get('user_id', 'Unknown')
            ccount = user.get('ccount', 0)
            response += f"{rank}. User ID: {user_id} - ccount: {ccount}\n"

        await update.message.reply_text(response)

    except Exception as e:
        # Handle errors and notify the admin
        await update.message.reply_text(f"An error occurred: {e}")

# Add the command handler to the application
application.add_handler(CommandHandler("topusers", top_users))

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import user_collection, user_count, application 
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import user_count

async def get_user_rarity_counts(update: Update, context: CallbackContext):
    # Replace YOUR_ADMIN_ID with your Telegram user ID or list of admin IDs
    

    # Restrict the command to admins
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    try:
        # Ensure the user ID is provided as an argument
        if not context.args:
            await update.message.reply_text("Please provide a user ID. Usage: /gtu <user_id>")
            return

        try:
            user_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("Invalid user ID. Please provide a valid numerical ID.")
            return

        # Fetch rarity counts for the specified user
        user_data = await user_count.find_one({'user_id': user_id})
        if not user_data or 'rarity_counts' not in user_data:
            await update.message.reply_text(f"No rarity data found for user ID: {user_id}.")
            return

        rarity_counts = user_data['rarity_counts']
        response = f"Rarity counts for user ID {user_id}:\n" + "\n".join(
            [f"{rarity}: {count}" for rarity, count in rarity_counts.items()]
        )

        await update.message.reply_text(response)

    except Exception as e:
        # Log error and inform the user
        await update.message.reply_text(f"An error occurred: {e}")

# Add the command handler
application.add_handler(CommandHandler("gtu1", get_user_rarity_counts))

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import user_count

async def get_user_rarity_counts(update: Update, context: CallbackContext):
    # Replace YOUR_ADMIN_ID with your Telegram user ID or list of admin IDs
    
    # Restrict the command to admins
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    try:
        # Ensure the user ID is provided as an argument
        if not context.args:
            await update.message.reply_text("Please provide a user ID. Usage: /gtu <user_id>")
            return

        try:
            user_id = context.args[0]
        except ValueError:
            await update.message.reply_text("Invalid user ID. Please provide a valid numerical ID.")
            return

        # Fetch rarity counts for the specified user
        user_data = await user_count.find_one({'user_id': user_id})
        if not user_data or 'rarity_counts' not in user_data:
            await update.message.reply_text(f"No rarity data found for user ID: {user_id}.")
            return

        rarity_counts = user_data['rarity_counts']
        response = f"Rarity counts for user ID {user_id}:\n" + "\n".join(
            [f"{rarity}: {count}" for rarity, count in rarity_counts.items()]
        )

        await update.message.reply_text(response)

    except Exception as e:
        # Log error and inform the user
        await update.message.reply_text(f"An error occurred: {e}")

# Add the command handler
application.add_handler(CommandHandler("gtu2", get_user_rarity_counts))



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


from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import user_collection, user_count

# Admin IDs for restricted access
# Replace with actual admin user IDs

# Rarity counts initialized to zero
rarity_counts = {
    "⚪️ Common": 0,
    "🟣 Rare": 0,
    "🟡 Legendary": 0,
    "🟢 Medium": 0,
    "💮 Special Edition": 0,
    "🔮 Limited Edition": 0,
    "💸 Premium Edition": 0,
    "🌤 Summer": 0,
    "🎐 Celestial": 0,
    "❄️ Winter": 0,
    "💝 Valentine": 0,
    "🎃 Halloween": 0,
    "🎄 Christmas Special": 0,
    "🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐": 0,
    "🎭 Cosplay Master 🎭": 0,
    "🎖 Apex Lot ( AUCTION )": 0,
    "🎗️ 𝘼𝙣𝙞𝙢𝙖𝙩𝙚𝙙":0
}

async def ucount_rall(update: Update, context: CallbackContext):
    # Restrict the command to admins
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    # Initialize counters
    processed_users = 0
    skipped_users = 0
    batch_size = 50  # Process in batches for better performance

    try:
        # Fetch all users from user_collection
        cursor = user_collection.find({'id': {'$exists': True, '$ne': None}})

        async for user in cursor:
            # Directly use user['id'] as 'id' is guaranteed to exist and be non-null
            user_id = user['id']

            # Check if the user_id is already in user_count and if rarity_counts already exists
            user_exists = await user_count.find_one({'user_id': user_id})
            if user_exists and 'rarity_counts' in user_exists:
                skipped_users += 1
                continue  # Skip users already in user_count with existing rarity_counts

            # Count the number of characters the user has
            
            # Calculate the rarity counts
            for character in user.get('characters', []):
                rarity = character.get('rarity')
                if rarity in rarity_counts:
                    rarity_counts[rarity] += 1

            # Prepare the new document for insertion or update
            document = {
                'user_id': user_id,
                'rarity_counts': rarity_counts.copy()  # Make a copy to avoid altering the original counts
            }

            # Update or insert the user's character count and rarity counts in user_count
            await user_count.update_one(
                {'user_id': user_id},  # Match user by ID
                {'$set': document},    # Insert or update with this document
                upsert=True            # Create new document if not present
            )

            processed_users += 1
            rarity_counts.clear()  # Reset the counts for the next user

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
application.add_handler(CommandHandler("rall", ucount_rall))


from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import user_count

async def get_user_rarity_counts(update: Update, context: CallbackContext):
    # Replace YOUR_ADMIN_ID with your Telegram user ID or list of admin IDs
    
    # Restrict the command to admins
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    # Extract the user_id from the command argument, if provided
    user_id = context.args[0] if context.args else None
    if not user_id:
        await update.message.reply_text("Please provide a valid user ID.")
        return

    try:
        # Query the user_count collection to find the user's data
        user_data = await user_count.find_one({'user_id': user_id})

        if user_data and 'rarity_counts' in user_data:
            rarity_data = user_data['rarity_counts']
            response_text = "Rarity Counts for User:\n"
            for rarity, count in rarity_data.items():
                response_text += f"{rarity}: {count}\n"
            await update.message.reply_text(response_text)
        else:
            await update.message.reply_text("No rarity data found for this user.")

    except Exception as e:
        # Handle errors gracefully
        await update.message.reply_text(f"An error occurred: {e}")

# Add the command handler
application.add_handler(CommandHandler("rcount", get_user_rarity_counts))


from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import main_count, collection

async def count_collection(update: Update, context: CallbackContext):
    # Replace YOUR_ADMIN_ID with your Telegram user ID or list of admin IDs
    
    # Restrict the command to admins
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    try:
        # Count all items in the collection directly
        total_items = await collection.count_documents({})

        # Store the total count directly in main_count
        document = {
            'id': 'collection_count',
            'total_items': total_items,
            'rarity_counts': {}  # To be updated next
        }

        # Update main_count with the total count
        await main_count.update_one(
            {'id': 'collection_count'},  # Unique identifier for this document
            {'$set': document},          # Insert or update with this document
            upsert=True                  # Create new document if not present
        )

        # Fetch rarity counts
        rarity_counts = {
            "⚪️ Common": 0,
            "🟣 Rare": 0,
            "🟡 Legendary": 0,
            "🟢 Medium": 0,
            "💮 Special Edition": 0,
            "🔮 Limited Edition": 0,
            "💸 Premium Edition": 0,
            "🌤 Summer": 0,
            "🎐 Celestial": 0,
            "❄️ Winter": 0,
            "💝 Valentine": 0,
            "🎃 Halloween": 0,
            "🎄 Christmas Special": 0,
            "🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐": 0,
            "🎭 Cosplay Master 🎭": 0,
            "🎖 Apex Lot ( AUCTION )": 0,
            "🎗️ 𝘼𝙣𝙞𝙢𝙖𝙩𝙚𝙙": 0
        }

        # Aggregate rarity counts
        cursor = collection.aggregate([
            {'$unwind': '$rarities'},
            {'$group': {'_id': '$rarities', 'count': {'$sum': 1}}}
        ])

        async for rarity in cursor:
            rarity_name = rarity['_id']
            if rarity_name in rarity_counts:
                rarity_counts[rarity_name] = rarity['count']

        # Update rarity_counts in main_count
        document['rarity_counts'] = rarity_counts
        await main_count.update_one(
            {'id': 'collection_count'},  # Unique identifier for this document
            {'$set': document},          # Insert or update with this document
            upsert=True                  # Create new document if not present
        )

        # Confirmation message
        await update.message.reply_text(f"Total items in collection: {total_items}")

    except Exception as e:
        # Log error and inform the user
        await update.message.reply_text(f"An error occurred: {e}")

# Add the command handler to the application
application.add_handler(CommandHandler("countn", count_collection))


from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import main_count

async def view_collection_count(update: Update, context: CallbackContext):
    # Replace YOUR_ADMIN_ID with your Telegram user ID or list of admin IDs
    

    # Restrict the command to admins
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    try:
        # Fetch the document from main_count
        document = await main_count.find_one({'id': 'collection_count'})

        if document:
            total_items = document.get('total_items', 0)
            rarity_counts = document.get('rarity_counts', {})

            # Prepare the message
            response_message = f"Total items in collection: {total_items}\n\nRarity Counts:\n"
            for rarity, count in rarity_counts.items():
                response_message += f"{rarity}: {count}\n"

            await update.message.reply_text(response_message)
        else:
            await update.message.reply_text("No collection count found in the database.")

    except Exception as e:
        # Log error and inform the user
        await update.message.reply_text(f"An error occurred: {e}")

# Add the command handler to the application
application.add_handler(CommandHandler("viewcc", view_collection_count))

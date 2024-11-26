from shivu import ban_collection, user_collection, banned_collection, PARTNER
from shivu import shivuu
from pyrogram import Client, filters
from pyrogram.types import Message


@shivuu.on_message(filters.command("nban"))
async def ban_user(_, message: Message):
    user_id = None
    if str(message.from_user.id) not in PARTNER:
        return

    # Check if the message is a reply
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    # If not a reply, check if a username or ID is provided in the command
    elif len(message.command) > 1:
        input_data = message.command[1]
        # Check if the input is a valid user ID
        if input_data.isdigit():
            user_id = int(input_data)
        else:
            # Try to fetch the user by username
            try:
                user = await shivuu.get_users(input_data)
                user_id = user.id
            except Exception as e:
                return await message.reply_text(f"❗️ Unable to find user: {input_data}")

    # If no user ID could be determined, send an error message
    if not user_id:
        return 

    # Check if the user is already banned
    existing_ban = await ban_collection.find_one({"user_id": user_id})
    if existing_ban:
        return 

    # Move user document from user_collection to banned_collection

       
    
    # Insert the user ID into the ban_collection
    await ban_collection.insert_one({"user_id": user_id})
  


@shivuu.on_message(filters.command("nunban"))
async def unban_user(_, message: Message):
    user_id = None
    if str(message.from_user.id) not in PARTNER:
        return

    # Check if the message is a reply
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    # If not a reply, check if a username or ID is provided in the command
    elif len(message.command) > 1:
        input_data = message.command[1]
        # Check if the input is a valid user ID
        if input_data.isdigit():
            user_id = int(input_data)
        else:
            # Try to fetch the user by username
            try:
                user = await shivuu.get_users(input_data)
                user_id = user.id
            except Exception as e:
                return await message.reply_text(f"❗️ Unable to find user: {input_data}")

    # If no user ID could be determined, send an error message
    if not user_id:
        return 

    # Check if the user is actually banned
    existing_ban = await ban_collection.find_one({"user_id": user_id})
    if not existing_ban:
        return await message.reply_text("🚫 User is not banned.")

    # Move user document from banned_collection to user_collection
    banned_data = await banned_collection.find_one({"user_id": user_id})
    if banned_data:
        await user_collection.insert_one(banned_data)
        await banned_collection.delete_one({"user_id": user_id})
    
    # Remove the user from the ban_collection
    await ban_collection.delete_one({"user_id": user_id})
    await message.reply_text(f"✅ User {user_id} has been unbanned.")


@shivuu.on_message(filters.command("checkbans"))
async def check_banned_users(_, message: Message):
    if str(message.from_user.id) not in PARTNER:
        return
    
    # Fetch all banned users
    banned_users = await ban_collection.find().to_list(length=None)

    # Check if there are no banned users
    if not banned_users:
        return await message.reply_text("📝 No users are currently banned.")

    # Prepare the response message
    response_text = "🚫 **Banned Users List:**\n\n"
    for user in banned_users:
        response_text += f"- User ID: `{user['user_id']}`\n"

    # Send the list of banned users
    await message.reply_text(response_text)


from shivu import banned_collection, PARTNER
from shivu import shivuu
from pyrogram import filters
from pyrogram.types import Message

@shivuu.on_message(filters.command("clearbans"))
async def clear_banned_collection(_, message: Message):
    # Check if the user is authorized (in the PARTNER list)
    if str(message.from_user.id) not in PARTNER:
        return

    await banned_collection.delete_many({})

        # Send a success message
    await message.reply_text("✅ All banned users have been cleared from the collection.")
    

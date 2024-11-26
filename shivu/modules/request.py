from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from datetime import datetime, timedelta
from shivu import shivuu as app, user_collection, collection  # Importing from shivu

# Global variables
support_chat_id = "-1002290598537"  # Your support/admin chat ID

# Handler for /request command (limit to 2 times a day)
@app.on_message(filters.command("request"))
async def request_character(client, message: Message):
    user_id = message.from_user.id
    current_time = datetime.utcnow()
    
    # Check if the user has already made requests today
    user_data = await user_collection.find_one({"id": user_id})
    
    if not user_data:
        # If user doesn't exist, create a new record
        user_data = {"id": user_id, "request_count": 0, "last_request_date": None}
    
    last_request_date = user_data.get("last_request_date")
    request_count = user_data.get("request_count", 0)

    # Check if the last request was today
    if last_request_date:
        last_request_datetime = datetime.strptime(last_request_date, "%Y-%m-%d")
        if last_request_datetime.date() == current_time.date():
            # If today and request count >= 2, deny the request
            if request_count >= 2:
                await message.reply_text("🚫 You have already made 2 requests today. Please try again tomorrow.")
                return
        else:
            # If it's a new day, reset the request count and date
            request_count = 0

    # Proceed with the request
    character_id = message.command[1]  # Assuming character ID is passed as a command argument
    character = await collection.find_one({"id": character_id})
    
    if not character:
        await message.reply_text("🚨 **Character not found.**")
        return

    # Message for the user with join link
    user_message = (
        f"👤 <b>Requested by:</b> {message.from_user.first_name} (<code>{user_id}</code>)\n\n"
        f"✨ <b>Your request for character</b> <i>'{character.get('name')}'</i> <b>has been successfully sent!</b>\n"
        f"🔗 <a href='https://t.me/+xJdjLviEJvpmYjM9'>Join</a>"
    )

    # Create Accept and Reject buttons
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Accept", callback_data=f"accept_{character_id}_{user_id}"),
         InlineKeyboardButton("❌ Reject", callback_data=f"reject_{character_id}_{user_id}")]
    ])

    # Send the message to the user with inline buttons
    await message.reply_text(user_message, disable_web_page_preview=True)

    # Send details to the support chat
    caption_message = (
        f"👤 <b>Requested by:</b> <a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>\n"
        f"🎴 <b>Character:</b> <b>{character.get('name', 'Unknown')}</b>\n"
        f"💎 <b>Rarity:</b> {character.get('rarity', 'Unknown')}\n"
        f"🆔 <b>Character ID:</b> <code>{character_id}</code>\n"
        f"@alone_x_hater"
    )
    
    support_message = await client.send_photo(
        chat_id=support_chat_id,
        photo=character.get('img_url', ''),
        caption=caption_message,
        reply_markup=buttons
    )

    # Store the request in the database
    await collection.update_one(
        {"id": character_id},
        {"$set": {"requester_id": str(user_id), "support_message_id": support_message.message_id}},
        upsert=True
    )

    # Increment the request count and update the last request date
    await user_collection.update_one(
        {"id": user_id},
        {
            "$set": {"last_request_date": current_time.strftime("%Y-%m-%d")},
            "$inc": {"request_count": 1}
        },
        upsert=True
    )


# Callback handler for Accept/Reject restricted to user 7378476666
@app.on_callback_query(filters.regex(r"^(accept|reject)_(\d+)_(.+)$"))
async def handle_request_response(client, callback_query: CallbackQuery):
    action, character_id, requester_id = callback_query.data.split("_")

    # Ensure only user with ID 7378476666 can accept or reject
    if callback_query.from_user.id != 7378476666:
        await callback_query.answer("❌ You don't have permission to perform this action.", show_alert=True)
        return

    # Handle requester_id as int or str
    try:
        requester_id = int(requester_id)
    except ValueError:
        requester_id = str(requester_id)

    # Query for character
    character = await collection.find_one({"id": character_id})
    if not character:
        await callback_query.answer("🚨 Request not found.", show_alert=True)
        return

    # Retrieve the support message ID for deletion
    request_data = await collection.find_one({"id": character_id})
    support_message_id = request_data.get("support_message_id") if request_data else None

    if action == "accept":
        # Add character to the requester's collection
        await user_collection.update_one(
            {'id': requester_id},
            {'$push': {'characters': character}}
        )
        await callback_query.answer("🎉 Request accepted!", show_alert=True)

        # Notify the requester
        await client.send_message(
            chat_id=requester_id,
            text=f"🎉 Your request for character '{character['name']}' has been accepted! "
                 f"You can check your collection using the /mycollection command."
        )

    elif action == "reject":
        await callback_query.answer("❌ Request rejected.", show_alert=True)

        # Notify the requester of rejection
        await client.send_message(
            chat_id=requester_id,
            text=f"❌ Your request for character '{character['name']}' was rejected."
        )

    # Clean up the request data in both cases (if needed)
    await collection.update_one(
        {"id": character_id},
        {"$unset": {"requester_id": "", "support_message_id": ""}}
    )
    
    # Delete the support message after acceptance or rejection
    if support_message_id:
        await client.delete_messages(chat_id=support_chat_id, message_ids=support_message_id)
    
    # Edit the original message to show the final status
    await callback_query.message.edit_text(
        f"Request for character <b>{character['name']}</b> has been {action}ed.",
        reply_markup=None  # Remove the buttons after action
    )

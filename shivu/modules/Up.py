import os
import requests
import motor.motor_asyncio
from pyrogram import Client, filters
from shivu import user_collection, collection
from shovu import shivuu as app
# Bot configuration
TARGET_GC_ID = -1002467462900
# Function to upload an image to Catbox
def upload_to_catbox(file_path):
    url = "https://catbox.moe/user/api.php"
    with open(file_path, "rb") as file:
        response = requests.post(url, data={"reqtype": "fileupload"}, files={"fileToUpload": file})
        if response.status_code == 200:
            return response.text.strip()
    return None

@app.on_message(filters.chat(TARGET_GC_ID) & filters.photo & filters.caption)
async def update_img_url(client, message):
    caption = message.caption.strip()
    if not caption.isdigit():
        await message.reply("Invalid caption! Please provide a numeric ID.")
        return

    char_id = int(caption)  # Extract the ID from the caption

    # Download the image
    file_path = await message.download()

    try:
        # Upload to Catbox
        catbox_url = upload_to_catbox(file_path)
        if not catbox_url:
            await message.reply("Failed to upload the image to Catbox.")
            return

        # Update the `img_url` field in the `collection`
        collection_update = await collection.update_one(
            {"id": char_id},  # Search by ID
            {"$set": {"img_url": catbox_url}}
        )

        # Update the `img_url` field in the `user_collection`
        user_collection_update = await user_collection.update_many(
            {"characters.id": char_id},  # Search characters by ID
            {"$set": {"characters.$.img_url": catbox_url}}
        )

        # Provide feedback
        if collection_update.modified_count > 0 or user_collection_update.modified_count > 0:
            await message.reply(f"Successfully updated the image URL for character ID `{char_id}`.")
        else:
            await message.reply(f"No matching character found for ID `{char_id}`.")
    finally:
        # Clean up the downloaded file
        if os.path.exists(file_path):
            os.remove(file_path)




@app.on_message(filters.command("del") & filters.user(7378476666))  # Restrict command to specific user
async def delete_character(client, message):
    # Extract character ID from the command
    if len(message.command) != 2:
        await message.reply("Usage: `/del <character_id>`\nExample: `/del abc123`", parse_mode="markdown")
        return

    char_id = message.command[1]  # Get the character ID as a string

    # Step 1: Delete the character from `anime_characters_lol`
    char_delete_result = await collection.delete_one({"id": char_id})

    # Step 2: Remove the character from users' collections in `user_collection`
    user_documents = await user_collection.find({"characters.id": char_id}).to_list(None)  # Find users with this character

    if user_documents:
        for user_doc in user_documents:
            await user_collection.update_one(
                {"_id": user_doc["_id"]},  # Identify the user
                {"$pull": {"characters": {"id": char_id}}}  # Remove the character from their list
            )

    # Step 3: Provide feedback
    if char_delete_result.deleted_count > 0 or user_documents:
        await message.reply(f"Successfully deleted character with ID `{char_id}` from the database and all user collections.")
    else:
        await message.reply(f"No character found with ID `{char_id}`.")


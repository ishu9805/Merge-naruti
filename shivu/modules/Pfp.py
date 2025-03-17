import os
import requests
from pyrogram import Client, filters

from . import app
from .block import block_dec, temp_block



from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from shivu import collection, user_collection
from shivu import LOG_CHANNEL as required_group_id

CATBOX_API_URL = "https://catbox.moe/user/api.php"

def upload_to_catbox(file_path: str) -> str:
    """
    Uploads a file to Catbox and returns the uploaded file URL.

    Args:
        file_path (str): Path to the file to upload.

    Returns:
        str: The URL of the uploaded file.

    Raises:
        Exception: If the upload fails.
    """
    try:
        with open(file_path, 'rb') as file:
            files = {'fileToUpload': file}
            data = {'reqtype': 'fileupload'}
            response = requests.post(CATBOX_API_URL, files=files, data=data)

        response_text = response.text.strip()

        if response.status_code == 200 and response_text.startswith('https://'):
            return response_text
        else:
            raise Exception(f"Catbox upload failed: {response_text}")
    except Exception as e:
        raise Exception(f"Error uploading to Catbox: {e}")

@app.on_message(filters.command("setpfp"))
@block_dec
async def set_profile_media(client: Client, message: Message):
    """
    Sets the replied photo as the user's profile media and sends it to the required group.
    """
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    reply_message = message.reply_to_message

    # Check if the message is a reply and contains a photo
    if not reply_message or not reply_message.photo:
        await message.reply_text("**❌ Please reply to a photo to set it as your profile media.**")
        return

    # Download the photo
    photo = reply_message.photo
    photo_path = await client.download_media(photo.file_id)

    try:
        # Upload the photo to Catbox
        img_url = upload_to_catbox(photo_path)
        await user_collection.update_one({'id': user_id}, {'$set': {'profile_media': img_url}})

        # Send the photo to the required group with a caption and buttons
        caption = f"**📸 New Profile Media Set!**\n\n"
        caption += f"👤 **User ID:** `{user_id}`\n"
        caption += f"🔗 **Image URL:** [View Image]({img_url})"

        # Create inline buttons
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("❌ Delete Profile Media", callback_data=f"delete_pfp_{user_id}")
                ]
            ]
        )

        await client.send_photo(
            chat_id=-1002338924488,
            photo=img_url,
            caption=caption,
            reply_markup=buttons
        )

        await message.reply_text("**✅ Profile media has been set!**")
    except Exception as e:
        await message.reply_text(f"**❌ Failed to upload image to Catbox: {e}**")
    finally:
        # Clean up the downloaded file
        if os.path.exists(photo_path):
            os.remove(photo_path)

@app.on_callback_query(filters.regex(r"^delete_pfp_(\d+)$"))
async def delete_profile_media_callback(client, callback_query):
    """
    Handles the callback query to delete the user's profile media.
    """
    user_id = int(callback_query.data.split("_")[2])  # Extract user ID from callback data

    # Check if the user is authorized to delete (e.g., admin or specific user)
    if callback_query.from_user.id == 7378476666:  # Replace with your user ID or admin check logic
        # Delete the profile media
        await user_collection.update_one({'id': user_id}, {'$unset': {'profile_media': ""}})
        await callback_query.answer("✅ Profile media has been deleted.")
    else:
        return #await callback_query.answer("")

    # Edit the message to remove the buttons
    await callback_query.message.edit_reply_markup(reply_markup=None)
    


@app.on_message(filters.command("delpfp"))
@block_dec
async def delete_profile_media(client: Client, message: Message):
    user_id = message.from_user.id
    user_data = await user_collection.find_one({'id': user_id})

    if not user_data or 'profile_media' not in user_data:
        await message.reply_text("No profile media found to delete.")
        return

    await user_collection.update_one({'id': user_id}, {'$unset': {'profile_media': ""}})
    await message.reply_text(f"**Profile media has been deleted.**")

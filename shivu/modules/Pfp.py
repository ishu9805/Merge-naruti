import os
import logging
import requests
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from shivu import collection, user_collection, LOG_CHANNEL as required_group_id
from . import app
from .block import block_dec, temp_block
from . import top_global_groups_collection as bot_chats
from .lock import command_lock as cmd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CATBOX_API_URL = "https://catbox.moe/user/api.php"

def upload_to_catbox(file_path: str) -> str:
    """
    Uploads a file to Catbox and returns the uploaded file URL.
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
        logger.error(f"Error uploading to Catbox: {e}")
        raise

@app.on_message(filters.command("setpfp"))
@block_dec
async def set_profile_media(client: Client, message: Message):
    """
    Sets the replied photo as the user's profile media and sends it to the admin group for approval.
    """
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    reply_message = message.reply_to_message

    if not reply_message or not reply_message.photo:
        await message.reply_text("**❌ Please reply to a photo to set it as your profile media.**")
        return

    photo = reply_message.photo
    photo_path = await client.download_media(photo.file_id)

    try:
        img_url = upload_to_catbox(photo_path)

        # Send the photo to the admin group with Approve and Reject buttons
        caption = f"**📸 New Profile Media Request!**\n\n"
        caption += f"👤 **User ID:** `{user_id}`\n"
        caption += f"📎 **Media URL:** {img_url}\n"
        caption += f" @sashta_dev"

        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"approve_pfp_{user_id}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"reject_pfp_{user_id}")
                ]
            ]
        )

        await client.send_photo(
            chat_id=-1002338924488,
            photo=img_url,
            caption=caption,
            reply_markup=buttons
        )

        await message.reply_text("**✅ Your profile media has been sent for approval.**")
    except Exception as e:
        logger.error(f"Failed to set profile media for user {user_id}: {e}")
        await message.reply_text(f"**❌ Failed to set profile media: {e}**")
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)

@app.on_callback_query(filters.regex(r"^approve_pfp_(\d+)$"))
async def approve_profile_media(client, callback_query):
    """
    Handles the callback query to approve the user's profile media.
    """
    user_id = int(callback_query.data.split("_")[2])

    # Check if the user is authorized to approve (e.g., admin)
    if callback_query.from_user.id == 7378476666:  # Replace with your admin check logic
        # Update the user's profile media in the database
        await user_collection.update_one({'id': user_id}, {'$set': {'profile_media': img_url}})
        await callback_query.answer("✅ Profile media approved.")

        # Notify the user
        await client.send_message(user_id, "**✅ Your profile media has been approved!**")
    else:
        await callback_query.answer("❌ You are not authorized to approve this.", show_alert=True)

    # Remove the buttons from the message
    await callback_query.message.edit_reply_markup(reply_markup=None)

@app.on_callback_query(filters.regex(r"^reject_pfp_(\d+)$"))
async def reject_profile_media(client, callback_query):
    """
    Handles the callback query to reject the user's profile media.
    """
    user_id = int(callback_query.data.split("_")[2])

    # Check if the user is authorized to reject (e.g., admin)
    if callback_query.from_user.id == 7378476666:  # Replace with your admin check logic
        await callback_query.answer("❌ Profile media rejected.")

        # Notify the user
        await client.send_message(user_id, "**❌ Your profile media has been rejected.**")
    else:
        await callback_query.answer("❌ You are not authorized to reject this.", show_alert=True)

    # Remove the buttons from the message
    await callback_query.message.edit_reply_markup(reply_markup=None)

@app.on_message(filters.command("delpfp"))
@block_dec
async def delete_profile_media(client: Client, message: Message):
    """
    Deletes the user's profile media.
    """
    user_id = message.from_user.id
    user_data = await user_collection.find_one({'id': user_id})

    if not user_data or 'profile_media' not in user_data:
        await message.reply_text("No profile media found to delete.")
        return

    await user_collection.update_one({'id': user_id}, {'$unset': {'profile_media': ""}})
    await message.reply_text("**✅ Profile media has been deleted.**")


from pyrogram import filters
from shivu import shivuu as app
import requests
import os
# Function to upload a file to Catbox
def upload_to_catbox(file_path):
    url = "https://catbox.moe/user/api.php"
    with open(file_path, "rb") as file:
        response = requests.post(
            url,
            data={"reqtype": "fileupload"},
            files={"fileToUpload": file}
        )
        if response.status_code == 200 and response.text.startswith("https"):
            return response.text
        else:
            raise Exception(f"Error uploading to Catbox: {response.text}")
@app.on_message(filters.command("tgm") & filters.reply)
async def send_catbox_link(client, message):
    reply = message.reply_to_message
    if reply and (reply.photo or reply.document):  # Check if the replied message contains a photo or document
        try:
            # Download the replied media
            path = await reply.download()
            # Check if the file is a PNG image or other file type
            if path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.pdf', '.docx')):
                # Upload the file to Catbox
                catbox_url = upload_to_catbox(path)
                # Send the Catbox link directly
                await message.reply(
                    text=f"Yᴏᴜʀ ʟɪɴᴋ sᴜᴄᴄᴇssғᴜʟ Gᴇɴ: {catbox_url}"
                )
            else:
                await message.reply("Please reply to a valid image (PNG, JPG, etc.) or document (PDF, DOCX).")
        except Exception as e:
            await message.reply(f"Failed to upload file. Error: {str(e)}")
        finally:
            # Ensure cleanup of the downloaded file
            if os.path.exists(path):
                os.remove(path)
    else:
        await message.reply("Please reply to a photo or a document.")
      

from shivu import shivuu as app
from pyrogram import filters
from pyrogram.types import Message
import json
import re
import os
from datetime import datetime as dt

@app.on_message(filters.command("conti") & filters.reply)
async def convert_txt_to_json_command(_, message: Message):
    json_file_path = "output.json"

    try:
        if not message.reply_to_message.document:
            await message.reply_text("Please reply to a message that contains a .txt document.")
            return
        
        document = message.reply_to_message.document
        
        if not document.file_name.endswith('.txt'):
            await message.reply_text("Please reply to a .txt document.")
            return
        
        file_id = document.file_id
        downloaded_file = await app.download_media(file_id)

        # Convert the downloaded .txt file to JSON
        json_output = convert_txt_to_json(downloaded_file)

        if json_output is not None:
            # Save the JSON output to a file
            with open(json_file_path, 'w') as json_file:
                json.dump(json_output, json_file, indent=4)

            # Send the JSON file back to the user
            await app.send_document(
                chat_id=message.chat.id,
                document=json_file_path,
                caption="Here is your converted JSON file."
            )
        else:
            await message.reply_text("Failed to convert the file to JSON.")

    except json.JSONDecodeError as e:
        await message.reply_text(f"JSON parsing error: {str(e)}")
    except Exception as e:
        await message.reply_text(f"An error occurred: {str(e)}")
    finally:
        if os.path.exists(downloaded_file):
            os.remove(downloaded_file)
        if os.path.exists(json_file_path):
            os.remove(json_file_path)

def convert_txt_to_json(file_path):
    try:
        with open(file_path, 'r') as file:
            user_data = file.read().strip()

        # Clean and prepare the text for JSON conversion
        user_data = user_data.replace("'", '"')  # Replace single quotes with double quotes
        user_data = re.sub(r'ObjectId\("([0-9a-f]{24})"\)', r'"\1"', user_data)  # Convert ObjectId to string
        user_data = re.sub(r'(?<!")\s*([a-zA-Z0-9_]+)\s*:', r'"\1":', user_data)  # Quote keys
        user_data = re.sub(r':\s*"(.*?)\s*"', r': "\1"', user_data)  # Clean up values
        user_data = re.sub(r'" +"', r'"', user_data)  # Remove unnecessary spaces in strings

        # Correct URLs by removing misplaced double quotes
        user_data = re.sub(r'"(h"[^:]*://[^"]+)"', r'\1', user_data)

        # Convert datetime representations to strings
        user_data = re.sub(
            r'datetime\.datetime\((\d{4}), (\d{1,2}), (\d{1,2}), (\d{1,2}), (\d{1,2}), (\d{1,2}), (\d{1,6})\)',
            lambda m: f'"{dt(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)), int(m.group(7))).isoformat()}"',
            user_data
        )

        user_data = re.sub(r',\s*([}\]])', r'\1', user_data)  # Remove trailing commas

        print("Prepared JSON string:", user_data)  # Debugging line

        json_data = json.loads(user_data)  # Parse the cleaned-up JSON

        return json_data

    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    return None


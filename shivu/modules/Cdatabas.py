import os
import re
import aiohttp
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from shivu import shivuups as shivuu, collectionps as collection # your MongoDB collection

# ===================== Logging =====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===================== Config =====================
SOURCE_GROUP_ID = -1002784099298
IMGBB_API_KEY = "6d52008ec9026912f9f50c8ca96a09c3"
DOWNLOAD_DIR = "downloads"

# Ensure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ===================== Helper Functions =====================
async def upload_to_imgbb(file_path, api_key=IMGBB_API_KEY):
    """
    Upload image to ImgBB
    """
    url = "https://api.imgbb.com/1/upload"
    
    # Check file size first (max 32MB)
    file_size = os.path.getsize(file_path)
    if file_size > 32 * 1024 * 1024:
        raise Exception(f"File size ({file_size/1024/1024:.2f} MB) exceeds the 32 MB limit.")
    
    # Read the file
    with open(file_path, "rb") as file:
        file_data = file.read()
    
    # Create form data
    data = aiohttp.FormData()
    data.add_field('key', api_key)
    data.add_field('image', file_data, filename=os.path.basename(file_path))
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as response:
            result = await response.json()
            if response.status == 200 and result.get("success"):
                return result["data"]["url"]
            else:
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                raise Exception(f"ImgBB upload failed: {error_msg}")

def extract_details_from_caption(caption: str):
    """
    Extract character details from the caption
    """
    name_pattern = r"(?:🔹|•)?\s*Name:\s*(.+)"
    anime_pattern = r"(?:🔸|•)?\s*Anime:\s*(.+)"
    id_pattern = r"(?:🔹|•)?\s*ID:\s*(\d+)"
    rarity_pattern = r"(?:🔸|•)?\s*Rarity:\s*(.+)"

    name_match = re.search(name_pattern, caption)
    anime_match = re.search(anime_pattern, caption)
    id_match = re.search(id_pattern, caption)
    rarity_match = re.search(rarity_pattern, caption)

    if not all([name_match, anime_match, id_match, rarity_match]):
        return None

    return {
        "name": name_match.group(1).strip(),
        "anime": anime_match.group(1).strip(),
        "id": id_match.group(1).strip(),
        "rarity": rarity_match.group(1).strip()
    }

async def process_message(message: Message):
    """
    Process a single incoming message
    """
    if not message.photo or not message.caption:
        return False, "No photo or caption"
    
    details = extract_details_from_caption(message.caption)
    if not details:
        return False, "Caption format invalid"
    
    try:
        # Download photo
        file_path = await message.download(file_name=os.path.join(DOWNLOAD_DIR, f"{message.id}.jpg"))
        
        # Upload to ImgBB
        img_url = await upload_to_imgbb(file_path)
        
        # Prepare document
        doc = {
            "id": details["id"],
            "name": details["name"],
            "anime": details["anime"],
            "rarity": details["rarity"],
            "img_url": img_url
        }

        # Insert into MongoDB
        await collection.update_one({"id": details["id"]}, {"$set": doc}, upsert=True)
        
        logger.info(f"✅ Added {details['name']} ({details['id']}) to collection")
        return True, f"Added {details['name']} ({details['id']})"
    
    except Exception as e:
        logger.error(f"❌ Error processing message {message.id}: {str(e)}")
        return False, str(e)
    
    finally:
        # Cleanup downloaded file
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

# ===================== Commands =====================

#shivuu.on_message(filters.command("resetcollection"))
async def reset_collection(client, message: Message):
    """
    Clear all documents from the collection
    """
    try:
        result = await collection.delete_many({})
        await message.reply(f"🗑️ Cleared collection. Deleted {result.deleted_count} documents.")
        logger.info("Collection cleared successfully.")
    except Exception as e:
        await message.reply(f"❌ Failed to clear collection: {str(e)}")

# ===================== Message Handler =====================
@shivuu.on_message(filters.chat(SOURCE_GROUP_ID) & filters.photo)
async def handle_new_photo(client, message: Message):
    """
    Automatically process new photo messages from the group
    """
    success, info = await process_message(message)
    if success:
        await message.reply(f"✅ Added to collection: {info}")
    else:
        logger.warning(f"Skipped message {message.id}: {info}")

# ===================== Start Bot =====================

  

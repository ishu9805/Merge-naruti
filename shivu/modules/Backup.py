import json
import logging
from pyrogram import Client
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from bson import json_util  # For handling BSON types
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from shivu import applicationps as application, user_collectionps as user_collection, collectionps as collection
# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)
LOGGER = logging.getLogger(__name__)

# MongoDB connection

# Pyrogram client setup

# Target chat ID
TARGET_CHAT_ID = -1002519947327

async def generate_and_send_json():
    try:
        # Fetch data from MongoDB collections
        collection_data = await collectionps.find().to_list(None)
        user_collection_data = await user_collectionps.find().to_list(None)

        # Combine data into a dictionary
        data = {
            "collection": collection_data,
            "user_collection": user_collection_data,
        }

        # Save data to a JSON file using bson.json_util for handling BSON types
        json_filename = "data_export.json"
        with open(json_filename, "w") as json_file:
            json.dump(data, json_file, indent=4, default=json_util.default)

        LOGGER.info("JSON file created successfully.")

        # Send the JSON file to the target chat
        async with app:
            await app.send_document(
                chat_id=TARGET_CHAT_ID,
                document=json_filename,
                caption="Here is the exported data from MongoDB collections."
            )
            LOGGER.info(f"JSON file sent to chat {TARGET_CHAT_ID}.")

    except Exception as e:
        LOGGER.error(f"An error occurred: {e}")

# Command handler for /backup
async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Starting backup process...")
    await generate_and_send_json()
    await update.message.reply_text("Backup completed and sent to the target chat.")

# Main function to start the bot

    # Add the /backup command handler

application.add_handler(CommandHandler("backup", backup_command))

    # Start the bot
    


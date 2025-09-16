import json
import logging
import os
from datetime import datetime
from bson import ObjectId
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from shivu import applicationps as application, user_collectionps as user_collection, shivuups as app, collectionps as collection

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)
LOGGER = logging.getLogger(__name__)

# Configuration
TARGET_CHAT_ID = -1002519947327
ALLOWED_USER_IDS = {12345678, 6902029663}  # Add the recovery user ID
RECOVERY_USER_ID = 6902029663  # Specific user allowed to use /recover

async def recover_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /recover command - must reply to a backup file"""
    user = update.effective_user
    
    # Check if user is authorized
    if user.id != RECOVERY_USER_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        LOGGER.warning(f"Unauthorized recover attempt by user {user.id}")
        return
    
    # Check if the message is a reply
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "❌ Please reply to a backup file with this command.\n"
            "Usage: /recover (as a reply to a backup JSON file)"
        )
        return
    
    replied_message = update.message.reply_to_message
    
    # Check if the replied message contains a document
    if not replied_message.document:
        await update.message.reply_text("❌ The replied message must contain a backup JSON file.")
        return
    
    # Check if it's a JSON file
    document = replied_message.document
    if not document.file_name.endswith('.json'):
        await update.message.reply_text("❌ Please reply to a JSON backup file.")
        return

    try:
        await update.message.reply_text("🔄 Starting recovery process...")
        
        # Download the file
        file = await context.bot.get_file(document.file_id)
        download_path = f"recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        await file.download_to_drive(download_path)
        
        LOGGER.info(f"Downloaded backup file: {download_path}")
        
        # Read and parse the backup file
        with open(download_path, 'r') as f:
            backup_data = json.load(f)
        
        # Restore data to MongoDB
        recovery_stats = await restore_backup(backup_data)
        
        # Send success message with statistics
        stats_message = (
            f"✅ Recovery completed successfully!\n\n"
            f"📊 Recovery Statistics:\n"
            f"• Collections restored: {recovery_stats['collection_count']} items\n"
            f"• User data restored: {recovery_stats['user_collection_count']} items\n"
            f"• Total documents: {recovery_stats['total_count']} items\n"
            f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        await update.message.reply_text(stats_message)
        LOGGER.info(f"Recovery completed by user {user.id}: {recovery_stats}")
        
    except json.JSONDecodeError:
        await update.message.reply_text("❌ Invalid JSON file. Please provide a valid backup file.")
        LOGGER.error("Invalid JSON file during recovery")
    except Exception as e:
        error_msg = f"❌ Recovery failed: {str(e)}"
        await update.message.reply_text(error_msg)
        LOGGER.error(f"Recovery failed: {e}", exc_info=True)
    finally:
        # Clean up downloaded file
        if os.path.exists(download_path):
            try:
                os.remove(download_path)
                LOGGER.info(f"Cleaned up recovery file: {download_path}")
            except Exception as e:
                LOGGER.warning(f"Could not remove recovery file: {e}")

async def restore_backup(backup_data):
    """Restore backup data to MongoDB collections"""
    stats = {
        'collection_count': 0,
        'user_collection_count': 0,
        'total_count': 0
    }
    
    try:
        # Restore collection data
        if 'collection' in backup_data and backup_data['collection']:
            # Clear existing collection data (optional - you might want to keep both)
            # await collection.delete_many({})
            
            # Insert backup data
            result = await collection.insert_many(backup_data['collection'])
            stats['collection_count'] = len(result.inserted_ids)
            LOGGER.info(f"Restored {stats['collection_count']} items to collection")
        
        # Restore user_collection data
        if 'user_collection' in backup_data and backup_data['user_collection']:
            # Clear existing user collection data (optional)
            # await user_collection.delete_many({})
            
            # Insert backup data
            result = await user_collection.insert_many(backup_data['user_collection'])
            stats['user_collection_count'] = len(result.inserted_ids)
            LOGGER.info(f"Restored {stats['user_collection_count']} items to user_collection")
        
        stats['total_count'] = stats['collection_count'] + stats['user_collection_count']
        
        return stats
        
    except Exception as e:
        LOGGER.error(f"Error during backup restoration: {e}")
        raise

async def recover_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command for recovery functionality"""
    user = update.effective_user
    
    if user.id != RECOVERY_USER_ID:
        await update.message.reply_text("❌ You are not authorized to use recovery commands.")
        return
    
    help_text = (
        "🔧 Recovery System Help\n\n"
        "📋 Available Commands:\n"
        "• /recover - Restore data from a backup file (reply to a JSON file)\n"
        "• /recoverhelp - Show this help message\n\n"
        "📝 Usage:\n"
        "1. First, download a backup file from the backup chat\n"
        "2. Send the JSON file to any chat\n"
        "3. Reply to that file message with /recover\n\n"
        "⚠️ Warning:\n"
        "• This will add data to the database (does not delete existing data)\n"
        "• Make sure the backup file is valid and from a trusted source\n"
        "• Only use this when you need to restore lost data"
    )
    
    await update.message.reply_text(help_text)
  


application.add_handler(CommandHandler("recover", recover_command))
application.add_handler(CommandHandler("recoverhelp", recover_help_command))
    

from pymongo import ReturnDocument
from pyrogram.enums import ChatMemberStatus, ChatType
from shivu import user_totals_collection, shivuu, PARTNER
from pyrogram import Client, filters
from pyrogram.types import Message
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@shivuu.on_message(filters.command("ctime"))
async def change_time(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Check if user is in the PARTNER list
    if str(user_id) not in PARTNER:
        return

    # Ensure the command is used in a group or supergroup
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return

    try:
        args = message.command
        if len(args) != 2:
            await message.reply_text("Usage: /ctime <new_frequency>")
            return

        new_frequency = int(args[1])
        if new_frequency < 1:
            await message.reply_text("Frequency must be a positive number.")
            return

        # Update the message frequency in the database
        chat_frequency = await user_totals_collection.find_one_and_update(
            {'chat_id': str(chat_id)},
            {'$set': {'message_frequency': new_frequency}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        await message.reply_text(f'✅ Frequency updated to {new_frequency}.')
        await log_command_usage("ctime", user_id, chat_id, success=True)
    except ValueError:
        await message.reply_text('❌ Please provide a valid number.')
        await log_command_usage("ctime", user_id, chat_id, success=False, error="Invalid number format.")
    except Exception as e:
        await message.reply_text(f'❌ Failed to change message frequency. Error: {str(e)}')
        await log_command_usage("ctime", user_id, chat_id, success=False, error=str(e))

async def log_command_usage(command: str, user_id: int, chat_id: int, success: bool, error: str = None):
    if success:
        logger.info(f"Command '{command}' used by user {user_id} in chat {chat_id} succeeded.")
    else:
        logger.error(f"Command '{command}' used by user {user_id} in chat {chat_id} failed. Error: {error}")

from pyrogram import Client, filters

# Initialize the Pyrogram client
from shivu import shivuu as app

# Log channel ID (replace with your channel ID)
LOG_CHANNEL_ID = -1002455650183

async def leave_group_and_log(group, count):
    """Leave the group and send a log to the log channel."""
    try:
        # Leave the group
        chat = await app.get_chat(group)
    
        await app.leave_chat(group)
        # Send a log message to the log channel
        log_message = f"Left group: {chat.title} (ID: {group}, Members: {count})"
        await app.send_message(LOG_CHANNEL_ID, log_message)
        #print(log_message)
    except Exception as e:
        error_message = f"Error leaving group {chat.title}: {e}"
        await app.send_message(LOG_CHANNEL_ID, error_message)
        #print(error_message)

@app.on_message(filters.group)
async def handle_new_message(client, message):
    """Handle incoming messages."""
    group = message.chat.id
    count = await app.get_chat_members_count(group)

    # Check the number of members in the group
    if count < 30:
    # Your logic here
        # Leave the group and log the action
        await leave_group_and_log(group, count)

# Start the client

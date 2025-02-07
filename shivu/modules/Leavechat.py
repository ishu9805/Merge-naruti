from pyrogram import Client, filters

# Initialize the Pyrogram client
from shivu import shivuu as app

# Log channel ID (replace with your channel ID)
LOG_CHANNEL_ID = -1002455650183

async def leave_group_and_log(group):
    """Leave the group and send a log to the log channel."""
    try:
        # Leave the group
        await app.leave_chat(group.id)
        # Send a log message to the log channel
        log_message = f"Left group: {group.title} (ID: {group.id}, Members: {group.members_count})"
        await app.send_message(LOG_CHANNEL_ID, log_message)
        #print(log_message)
    except Exception as e:
        error_message = f"Error leaving group {group.title}: {e}"
        await app.send_message(LOG_CHANNEL_ID, error_message)
        #print(error_message)

@app.on_message(filters.group)
async def handle_new_message(client, message):
    """Handle incoming messages."""
    group = message.chat
    # Check the number of members in the group
    if group.members_count < 30:
        # Leave the group and log the action
        await leave_group_and_log(group)

# Start the client

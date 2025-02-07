from telethon import TelegramClient, events
from telethon.tl.functions.channels import LeaveChannelRequest

from shivu import app as client
# Log channel ID (replace with your channel ID)
LOG_CHANNEL_ID = -1002455650183

# 
async def leave_group_and_log(group):
    """Leave the group and send a log to the log channel."""
    try:
        # Leave the group
        await client(LeaveChannelRequest(group))
        # Send a log message to the log channel
        log_message = f"Left group: {group.title} (ID: {group.id}, Members: {group.participants_count})"
        await client.send_message(LOG_CHANNEL_ID, log_message)
        print(log_message)
    except Exception as e:
        error_message = f"Error leaving group {group.title}: {e}"
        await client.send_message(LOG_CHANNEL_ID, error_message)
        print(error_message)

@client.on(events.NewMessage)
async def handle_new_message(event):
    """Handle incoming messages."""
    # Check if the message is from a group or channel
    if event.is_group or event.is_channel:
        # Get the group/channel entity
        group = await event.get_chat()
        # Check the number of members in the group
        if group.participants_count < 30:
            # Leave the group and log the action
            await leave_group_and_log(group)
        else:
            return 

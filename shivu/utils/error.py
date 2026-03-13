import logging
from functools import wraps

from telegram import Update
from telegram.ext import CallbackContext

from shivu.logging_utils import send_ptb_log

LOGGER = logging.getLogger(__name__)


def error(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            error_message = f"An error occurred: {e}"
            LOGGER.exception("Unhandled error in wrapped PTB function")
            await send_ptb_log(context.bot, f"#ERROR\nwrapper={func.__name__}\nerror={type(e).__name__}: {e}")
            if update.message:
                await update.message.reply_text(error_message, parse_mode='HTML')
            elif update.callback_query:
                await update.callback_query.message.reply_text(error_message, parse_mode='HTML')

    return wrapper

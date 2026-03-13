import logging
import traceback
from moto.Config import LOG_CHANNEL

LOGGER = logging.getLogger(__name__)
MAX_LOG_LENGTH = 3500


def _truncate(text: str, limit: int = MAX_LOG_LENGTH) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit]}\n...<truncated>"


async def send_pyrogram_log(client, text: str) -> None:
    try:
        await client.send_message(chat_id=LOG_CHANNEL, text=_truncate(text), disable_web_page_preview=True)
    except Exception:
        LOGGER.exception("Failed to send pyrogram log to log channel")


async def send_ptb_log(bot, text: str) -> None:
    try:
        await bot.send_message(chat_id=LOG_CHANNEL, text=_truncate(text), disable_web_page_preview=True)
    except Exception:
        LOGGER.exception("Failed to send PTB log to log channel")


async def log_pyrogram_exception(client, message, handler_name: str, error: Exception) -> None:
    user = getattr(message, "from_user", None)
    chat = getattr(message, "chat", None)
    tb = traceback.format_exc()
    await send_pyrogram_log(
        client,
        (
            "#ERROR\n"
            f"handler={handler_name}\n"
            f"chat_id={getattr(chat, 'id', 'unknown')}\n"
            f"user_id={getattr(user, 'id', 'unknown')}\n"
            f"error={type(error).__name__}: {error}\n\n"
            f"traceback:\n{tb}"
        ),
    )


async def log_ptb_exception(update, context, error: Exception) -> None:
    chat = update.effective_chat if update else None
    user = update.effective_user if update else None
    tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    await send_ptb_log(
        context.bot,
        (
            "#ERROR\n"
            "framework=ptb\n"
            f"chat_id={getattr(chat, 'id', 'unknown')}\n"
            f"user_id={getattr(user, 'id', 'unknown')}\n"
            f"error={type(error).__name__}: {error}\n\n"
            f"traceback:\n{tb}"
        ),
    )

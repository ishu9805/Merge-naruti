import os
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, WebAppInfo as PyroWebAppInfo
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import CallbackContext, CommandHandler

from shivu import shivuups as app, applicationps as application
from shivu.modules.block import block_dec, block_dec_ptb

MINI_APP_URL = os.getenv("MINI_APP_URL", "https://bladeweb-files.onrender.com")


def build_miniapp_keyboard_ptb():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🌐 Open Mini App", web_app=WebAppInfo(url=MINI_APP_URL))],
            [InlineKeyboardButton("🔗 Open in Browser", url=MINI_APP_URL)],
        ]
    )


def build_miniapp_keyboard_pyro():
    return IKM(
        [
            [IKB("🌐 Open Mini App", web_app=PyroWebAppInfo(url=MINI_APP_URL))],
            [IKB("🔗 Open in Browser", url=MINI_APP_URL)],
        ]
    )


@block_dec_ptb
async def miniapp_ptb(update: Update, context: CallbackContext):
    if not update.effective_message:
        return
    await update.effective_message.reply_text(
        "🚀 Launch the Naruto Collection Mini App to browse bot database, user collections, shop templates, and leaderboard.",
        reply_markup=build_miniapp_keyboard_ptb(),
    )


@app.on_message(filters.command("miniapp") & filters.private)
@block_dec
async def miniapp_pyro(_, message):
    await message.reply_text(
        "🚀 Launch the Naruto Collection Mini App to browse bot database, user collections, shop templates, and leaderboard.",
        reply_markup=build_miniapp_keyboard_pyro(),
    )


application.add_handler(CommandHandler("miniapp", miniapp_ptb, block=False))

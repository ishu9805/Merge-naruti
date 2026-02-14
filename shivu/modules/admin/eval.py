import os
import re
import asyncio
import subprocess
import sys
import traceback
from inspect import getfullargspec
from io import StringIO
from time import time
from shivu import dbps as db
from pyrogram import filters
from pyrogram.types import (InlineKeyboardButton,
                            InlineKeyboardMarkup, Message)

from shivu import shivuups as Client
from shivu.modules import dev_filter
from scap import capsify
from shivu.modules.block import block_cbq


async def aexec(code, client, message):
    exec(
        "async def __aexec(client, message): "
        + "".join(f"\n {a}" for a in code.split("\n"))
    )
    return await locals()["__aexec"](client, message)


async def edit_or_reply(msg: Message, **kwargs):
    func = msg.edit_text if msg.from_user.is_self else msg.reply
    spec = getfullargspec(func.__wrapped__).args
    await func(**{k: v for k, v in kwargs.items() if k in spec})


@Client.on_message(
    filters.command("eval")
    & dev_filter
)
async def executor(client, message):
    m = message
    if len(message.command) < 2:
        return await edit_or_reply(
            message, text=capsify("Give me some command to execute.")
        )
    try:
        cmd = message.text.split(" ", maxsplit=1)[1]
    except IndexError:
        return await message.delete()
    t1 = time()
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    redirected_error = sys.stderr = StringIO()
    stdout, stderr, exc = None, None, None
    try:
        await aexec(cmd, client, message)
    except Exception:
        exc = traceback.format_exc()
    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    evaluation = ""
    if exc:
        evaluation = exc
    elif stderr:
        evaluation = stderr
    elif stdout:
        evaluation = stdout
    else:
        evaluation = "Success"
    final_output = f"**OUTPUT**:\n`{evaluation.strip()}`"
    if len(final_output) > 4096:
        filename = "output.txt"
        with open(filename, "w+", encoding="utf8") as out_file:
            out_file.write(str(evaluation.strip()))
        t2 = time()
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="⏳",
                        callback_data=f"runtime {t2-t1} Seconds",
                    )
                ]
            ]
        )
        await message.reply_document(
            document=filename,
            caption=f"**INPUT:**\n`{cmd[0:980]}`\n\n**OUTPUT:**\n`Attached Document`",
            quote=False,
            reply_markup=keyboard,
        )
        await message.delete()
        os.remove(filename)
    else:
        t2 = time()
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="⏳",
                        callback_data=f"runtime {round(t2-t1, 3)} Seconds",
                    ),
                    InlineKeyboardButton(
                        text="🗑",
                        callback_data=f"eval_close_{m.from_user.id}",
                    ),
                ]
            ]
        )
        await edit_or_reply(
            message, text=final_output, reply_markup=keyboard
        )

@Client.on_callback_query(filters.regex(r"runtime"))
@block_cbq
async def runtime_func_cq(_, cq):
    runtime = cq.data.split(None, 1)[1]
    await cq.answer(runtime, show_alert=True)

@Client.on_message(
    filters.command("sh")
    & dev_filter
)
async def shellrunner(client, message):
    if len(message.command) < 2:
        return await edit_or_reply(
            message, text="**Usage:**\n/sh git pull"
        )
    text = message.text.split(None, 1)[1]
    if "\n" in text:
        code = text.split("\n")
        output = ""
        for x in code:
            shell = re.split(
                """ (?=(?:[^'"]|'[^']*'|"[^"]*")*$)""", x
            )
            try:
                process = subprocess.Popen(
                    shell,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            except Exception as err:
                await edit_or_reply(
                    message, text=f"**ERROR:**\n```{err}```"
                )
            output += f"**{code}**\n"
            output += process.stdout.read()[:-1].decode("utf-8")
            output += "\n"
    else:
        shell = re.split(""" (?=(?:[^'"]|'[^']*'|"[^"]*")*$)""", text)
        for a in range(len(shell)):
            shell[a] = shell[a].replace('"', "")
        try:
            process = subprocess.Popen(
                shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            errors = traceback.format_exception(
                etype=exc_type,
                value=exc_obj,
                tb=exc_tb,
            )
            return await edit_or_reply(
                message, text=f"**ERROR:**\n```{''.join(errors)}```"
            )
        output = process.stdout.read()[:-1].decode("utf-8")
    if str(output) == "\n":
        output = None
    if output:
        if len(output) > 4096:
            with open("output.txt", "w+") as file:
                file.write(output)
            await message.reply_document(
                "output.txt",
                caption="`Output`",
            )
            return os.remove("output.txt")
        await edit_or_reply(
            message, text=f"**OUTPUT:**\n```{output}```"
        )
    else:
        await edit_or_reply(message, text="**OUTPUT: **\n`No output`")


async def aexec_scheduled(code):
    exec(
        "async def __aexec(): " +
        "".join(f"\n {line}" for line in code.split("\n"))
    )
    return await locals()["__aexec"]()



@Client.on_message(
    filters.command("clearexec")
    & dev_filter
)
async def clear_exec(client, message: Message):
    removed = []
    # Remove dynamically created eval functions
    for key in list(globals().keys()):
        if key.startswith("__aexec"):
            del globals()[key]
            removed.append(key)

    # Remove temp files if any
    if os.path.exists("output.txt"):
        os.remove("output.txt")
        removed.append("output.txt")

    # Kill background processes if left running
    try:
        subprocess.run("pkill -f python", shell=True)
    except Exception:
        pass

    await message.reply_text(
        f"✅ Cleared executed code.\nRemoved: `{', '.join(removed) if removed else 'Nothing to remove'}`"
    )

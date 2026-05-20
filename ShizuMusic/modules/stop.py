# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from ShizuMusic import bot
from ShizuMusic.core.call import leave_vc
from ShizuMusic.core.queue import clear_queue, queue_size
from ShizuMusic.utils.permissions import is_user_authorized


# ─────────────────────────────────────────────
# STOP — Playback + Queue + AutoPlay Clear
# ─────────────────────────────────────────────
@bot.on_message(filters.group & filters.command(["stop", "end"]))
async def stop_cmd(_, message: Message) -> None:

    # Admin check
    if not await is_user_authorized(message):
        await message.reply(
            "<b>❍ ᴀᴅᴍɪɴ ᴏɴʟʏ</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    chat_id = message.chat.id

    # leave_vc also clears autoplay state
    await leave_vc(chat_id)

    await message.reply(
        "<b>❍ ᴘʟᴀʏʙᴀᴄᴋ ꜱᴛᴏᴘᴘᴇᴅ</b>\n"
        "<b>❍ Qᴜᴇᴜᴇ ᴄʟᴇᴀʀᴇᴅ</b>\n"
        "<b>❍ ʟᴇꜰᴛ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ</b>",
        parse_mode=ParseMode.HTML,
    )


# ─────────────────────────────────────────────
# CLEAR QUEUE (Without Leaving VC)
# ─────────────────────────────────────────────
@bot.on_message(filters.group & filters.command("clear"))
async def clear_cmd(_, message: Message) -> None:

    # Admin check
    if not await is_user_authorized(message):
        await message.reply(
            "<b>❍ ᴀᴅᴍɪɴ ᴏɴʟʏ</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    chat_id = message.chat.id

    # Stop autoplay while clearing queue
    try:
        from ShizuMusic.core.autoplay import stop_autoplay
        stop_autoplay(chat_id)

    except Exception:
        pass

    # Queue empty
    if not queue_size(chat_id):
        await message.reply(
            "<b>❍ Qᴜᴇᴜᴇ ɪꜱ ᴇᴍᴘᴛʏ</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    # Clear queue
    clear_queue(chat_id)

    await message.reply(
        "<b>❍ Qᴜᴇᴜᴇ ᴄʟᴇᴀʀᴇᴅ</b>\n"
        "<b>❍ ᴀʟʟ ꜱᴏɴɢꜱ ʀᴇᴍᴏᴠᴇᴅ</b>",
        parse_mode=ParseMode.HTML,
    )


# ─────────────────────────────────────────────
# REBOOT
# ─────────────────────────────────────────────
@bot.on_message(filters.command("reboot"))
async def reboot_cmd(_, message: Message) -> None:

    chat_id = message.chat.id

    # Leave VC and reset states
    await leave_vc(chat_id)

    await message.reply(
        "<b>❍ ᴄʜᴀᴛ ʀᴇʙᴏᴏᴛᴇᴅ</b>\n"
        "<b>❍ ᴀʟʟ ꜱᴛᴀᴛᴇꜱ ʀᴇꜱᴇᴛ</b>",
        parse_mode=ParseMode.HTML,
    )

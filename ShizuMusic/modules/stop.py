# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

from pyrogram import filters
from pyrogram.types import Message

from ShizuMusic import bot
from ShizuMusic.core.call import leave_vc
from ShizuMusic.core.queue import clear_queue, queue_size
from ShizuMusic.modules.block import group_allowed, user_allowed
from ShizuMusic.utils.permissions import is_user_authorized
from ShizuMusic.utils.rich_ui import rich_heading, rich_note, rich_send


# ── /stop & /end ──────────────────────────────────────────────────────────────

@bot.on_message(
    filters.group
    & filters.command(["stop", "end"])
    & group_allowed
    & user_allowed
)
async def stop_cmd(_, message: Message) -> None:

    chat_id = message.chat.id

    if not await is_user_authorized(message):
        await rich_send(bot, chat_id, rich_heading("⛔ ᴀᴅᴍɪɴ ᴏɴʟʏ", level=3))
        return

    await leave_vc(chat_id)

    await rich_send(
        bot, chat_id,
        rich_heading("⏹ ᴘʟᴀʏʙᴀᴄᴋ sᴛᴏᴘᴘᴇᴅ", level=3)
        + rich_note("ǫᴜᴇᴜᴇ ᴄʟᴇᴀʀᴇᴅ · ʟᴇғᴛ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ"),
    )


# ── /clear ─────────────────────────────────────────────────────────────────────

@bot.on_message(
    filters.group
    & filters.command("clear")
    & group_allowed
    & user_allowed
)
async def clear_cmd(_, message: Message) -> None:

    chat_id = message.chat.id

    if not await is_user_authorized(message):
        await rich_send(bot, chat_id, rich_heading("⛔ ᴀᴅᴍɪɴ ᴏɴʟʏ", level=3))
        return

    try:
        from ShizuMusic.core.autoplay import stop_autoplay
        stop_autoplay(chat_id)
    except Exception:
        pass

    if not queue_size(chat_id):
        await rich_send(bot, chat_id, rich_heading("❍ ǫᴜᴇᴜᴇ ɪs ᴇᴍᴘᴛʏ", level=3))
        return

    clear_queue(chat_id)
    await rich_send(
        bot, chat_id,
        rich_heading("🧹 ǫᴜᴇᴜᴇ ᴄʟᴇᴀʀᴇᴅ", level=3)
        + rich_note("ᴀʟʟ sᴏɴɢs ʀᴇᴍᴏᴠᴇᴅ"),
    )


# ── /reboot ────────────────────────────────────────────────────────────────────

@bot.on_message(
    filters.command("reboot")
    & group_allowed
    & user_allowed
)
async def reboot_cmd(_, message: Message) -> None:
    chat_id = message.chat.id
    await leave_vc(chat_id)
    await rich_send(
        bot, chat_id,
        rich_heading("🔄 ᴄʜᴀᴛ ʀᴇʙᴏᴏᴛᴇᴅ", level=3)
        + rich_note("ᴀʟʟ sᴛᴀᴛᴇs ʀᴇsᴇᴛ"),
    )


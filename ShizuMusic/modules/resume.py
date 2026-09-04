# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

from pyrogram import filters
from pyrogram.types import Message

from ShizuMusic import bot, call_py
from ShizuMusic.modules.block import group_allowed, user_allowed
from ShizuMusic.utils.permissions import is_user_authorized
from ShizuMusic.utils.rich_ui import rich_esc, rich_heading, rich_note, rich_send


@bot.on_message(
    filters.group
    & filters.command("resume")
    & group_allowed
    & user_allowed
)
async def resume_cmd(_, message: Message) -> None:

    chat_id = message.chat.id

    if not await is_user_authorized(message):
        await rich_send(
            bot, chat_id,
            rich_heading("⛔ ᴀᴅᴍɪɴ ᴏɴʟʏ", level=3)
            + rich_note("ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪs ғᴏʀ ɢʀᴏᴜᴘ ᴀᴅᴍɪɴs."),
        )
        return

    try:
        await call_py.resume(chat_id)
        await rich_send(
            bot, chat_id,
            rich_heading("▶ sᴛʀᴇᴀᴍ ʀᴇsᴜᴍᴇᴅ", level=3)
            + rich_note("ᴍᴜsɪᴄ ᴘʟᴀʏʙᴀᴄᴋ ᴄᴏɴᴛɪɴᴜᴇᴅ."),
        )
    except Exception as e:
        await rich_send(
            bot, chat_id,
            rich_heading("❍ ʀᴇsᴜᴍᴇ ғᴀɪʟᴇᴅ", level=3)
            + rich_note(f"<code>{rich_esc(e)}</code>"),
        )


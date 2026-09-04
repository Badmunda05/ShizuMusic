# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from ShizuMusic import bot
from ShizuMusic.core.autoplay import (
    get_autoplay_query,
    is_autoplay,
    start_autoplay,
    stop_autoplay,
)
from ShizuMusic.core.call import leave_vc
from ShizuMusic.core.player import play_song
from ShizuMusic.core.queue import peek_current, queue_size
from ShizuMusic.modules.block import group_allowed, user_allowed
from ShizuMusic.utils.formatters import short
from ShizuMusic.utils.permissions import is_user_authorized
from ShizuMusic.utils.rich_ui import (
    rich_edit,
    rich_esc,
    rich_heading,
    rich_kv_table,
    rich_note,
    rich_send,
)


@bot.on_message(
    filters.group
    & filters.regex(r"^/autoplay(?:@\w+)?(?:\s+(?P<q>.+))?$")
    & group_allowed
    & user_allowed
)
async def autoplay_cmd(_, message: Message) -> None:

    chat_id = message.chat.id
    user    = message.from_user

    if not await is_user_authorized(message):
        await rich_send(
            bot, chat_id,
            rich_heading("⛔ ᴀᴅᴍɪɴ ᴏɴʟʏ", level=3)
            + rich_note("ᴏɴʟʏ ɢʀᴏᴜᴘ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ /autoplay"),
        )
        return

    match = message.matches[0]
    query = (match.group("q") or "").strip()

    if not query:
        current_q = get_autoplay_query(chat_id)
        if is_autoplay(chat_id) and current_q:
            await rich_send(
                bot, chat_id,
                rich_heading("🔁 ᴀᴜᴛᴏᴘʟᴀʏ ɪs ᴀʟʀᴇᴀᴅʏ ʀᴜɴɴɪɴɢ", level=3)
                + rich_kv_table([("ǫᴜᴇʀʏ", f"<code>{rich_esc(current_q)}</code>")])
                + rich_note("ᴜsᴇ /end ᴛᴏ sᴛᴏᴘ ᴀᴜᴛᴏᴘʟᴀʏ ғɪʀsᴛ"),
            )
        else:
            await rich_send(
                bot, chat_id,
                rich_heading("🔁 ᴀᴜᴛᴏᴘʟᴀʏ ᴜsᴀɢᴇ", level=3)
                + rich_kv_table([("ᴜsᴀɢᴇ", "<code>/autoplay sidhu moose wala</code>")])
                + rich_note("ᴛʜɪs ᴡɪʟʟ ᴄᴏɴᴛɪɴᴜᴏᴜsʟʏ ᴘʟᴀʏ sᴏɴɢs ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ"),
            )
        return

    pm = await rich_send(
        bot, chat_id,
        rich_heading("🔁 sᴇᴛᴛɪɴɢ ᴜᴘ ᴀᴜᴛᴏᴘʟᴀʏ...", level=3)
        + rich_kv_table([("ǫᴜᴇʀʏ", f"<code>{rich_esc(query)}</code>")]),
    )

    req    = user.first_name if user else "AutoPlay"
    req_id = user.id         if user else 0

    was_playing = queue_size(chat_id) > 0
    count       = await start_autoplay(chat_id, query, req, req_id)

    if count == 0:
        stop_autoplay(chat_id)
        await rich_edit(
            pm,
            rich_heading("❍ ᴀᴜᴛᴏᴘʟᴀʏ ғᴀɪʟᴇᴅ", level=3)
            + rich_note("ɴᴏ sᴏɴɢs ᴡᴇʀᴇ ғᴏᴜɴᴅ, ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ"),
        )
        return

    first = peek_current(chat_id)

    await rich_edit(
        pm,
        rich_heading("🔁 ᴀᴜᴛᴏᴘʟᴀʏ sᴛᴀʀᴛᴇᴅ", level=3)
        + rich_kv_table([
            ("ǫᴜᴇʀʏ", f"<code>{rich_esc(query)}</code>"),
            ("ᴀᴅᴅᴇᴅ", f"{count} sᴏɴɢs ᴛᴏ ǫᴜᴇᴜᴇ"),
        ])
        + rich_note("ᴜsᴇ /end ᴛᴏ sᴛᴏᴘ ᴀᴜᴛᴏᴘʟᴀʏ"),
    )

    if not was_playing and first:
        dm = await rich_send(
            bot, chat_id,
            rich_heading("❍ ɴᴏᴡ ᴘʟᴀʏɪɴɢ", level=3)
            + rich_kv_table([("ᴛɪᴛʟᴇ", f"<code>{rich_esc(short(first['title']))}</code>")]),
        )
        await play_song(chat_id, dm, first)

    try:
        await message.delete()
    except Exception:
        pass


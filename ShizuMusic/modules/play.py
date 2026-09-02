# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio
import re
import time

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import config
from ShizuMusic import bot
from ShizuMusic.core.player import play_song
from ShizuMusic.core.queue import add_to_queue, peek_current, queue_size
from ShizuMusic.modules.block import group_allowed, user_allowed
from ShizuMusic.utils.assistant import is_assistant_in, try_join_assistant
from ShizuMusic.utils.db import add_served_chat, add_served_user
from ShizuMusic.utils.formatters import fmt_time, iso_to_human, iso_to_sec, short
from ShizuMusic.utils.rich_ui import (
    rich_edit,
    rich_esc,
    rich_heading,
    rich_kv_table,
    rich_note,
    rich_send,
)
from ShizuMusic.utils.youtube import search_yt

# ── Blocked words ──────────────────────────────────────────────────────────────
BLOCKED_WORDS = [
    "porn", "xxx", "xnxx", "xvideos",
    "sex", "fuck", "lund",
    "drug", "cocaine", "weed", "charas",
]

# ── Per-chat state ─────────────────────────────────────────────────────────────
_last_cmd: dict[int, float] = {}
_pending:  dict[int, tuple] = {}


# ── DB helper ──────────────────────────────────────────────────────────────────

def _db_track(chat_id: int, user_id: int) -> None:
    try:
        add_served_chat(chat_id)
        if user_id:
            add_served_user(user_id)
    except Exception:
        pass


# ── Cooldown handler ───────────────────────────────────────────────────────────

async def _run_pending(chat_id: int, delay: int) -> None:
    await asyncio.sleep(delay)
    if chat_id in _pending:
        msg, reply = _pending.pop(chat_id)
        try:
            await reply.delete()
        except Exception:
            pass
        await play_handler(bot, msg)


# ── /play & /vplay command ─────────────────────────────────────────────────────

@bot.on_message(
    filters.group
    & filters.regex(r"^/(?P<cmd>v?play)(?:@\w+)?(?:\s+(?P<q>.+))?$")
    & group_allowed
    & user_allowed
)
async def play_handler(_, message: Message) -> None:

    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    _db_track(chat_id, user_id)

    # ── Replied audio / video ──────────────────────────────────────────────────
    if message.reply_to_message and (
        message.reply_to_message.audio or message.reply_to_message.video
    ):
        pm = await rich_send(bot, chat_id, rich_heading("❍ ᴘʀᴏᴄᴇssɪɴɢ ᴍᴇᴅɪᴀ...", level=3))

        orig  = message.reply_to_message
        fresh = await bot.get_messages(orig.chat.id, orig.id)
        media = fresh.video or fresh.audio

        if fresh.audio and getattr(fresh.audio, "file_size", 0) > 100 * 1024 * 1024:
            await rich_edit(
                pm,
                rich_heading("❍ ғɪʟᴇ ᴛᴏᴏ ʟᴀʀɢᴇ", level=3)
                + rich_kv_table([("ᴍᴀx", "<code>100 MB</code>")]),
            )
            return

        await rich_edit(pm, rich_heading("❍ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴍᴇᴅɪᴀ...", level=3))

        try:
            fp = await bot.download_media(media)
        except Exception as e:
            await rich_edit(
                pm,
                rich_heading("❍ ᴅᴏᴡɴʟᴏᴀᴅ ғᴀɪʟᴇᴅ", level=3)
                + rich_note(f"<code>{rich_esc(e)}</code>"),
            )
            return

        thumb = None
        try:
            thumbs = (fresh.video or fresh.audio).thumbs
            if thumbs:
                thumb = await bot.download_media(thumbs[0])
        except Exception:
            pass

        song = {
            "url":              fp,
            "title":            getattr(media, "file_name", "Audio"),
            "duration":         fmt_time(media.duration or 0),
            "duration_seconds": media.duration or 0,
            "requester":        message.from_user.first_name if message.from_user else "Unknown",
            "requester_id":     user_id,
            "thumbnail":        thumb,
        }

        add_to_queue(chat_id, song)
        await play_song(chat_id, pm, song)
        return

    # ── Text query ─────────────────────────────────────────────────────────────
    match = message.matches[0]
    query = (match.group("q") or "").strip()
    cmd   = (match.group("cmd") or "play").strip()

    try:
        await message.delete()
    except Exception:
        pass

    # Blocked words check
    if any(x in query.lower() for x in BLOCKED_WORDS):
        await rich_send(bot, chat_id, rich_heading("❍ ᴛʜɪs sᴏɴɢ ɪs ʙʟᴏᴄᴋᴇᴅ", level=3))
        return

    # Cooldown check
    now = time.time()
    if chat_id in _last_cmd and (now - _last_cmd[chat_id]) < config.COOLDOWN:
        rem = int(config.COOLDOWN - (now - _last_cmd[chat_id]))
        if chat_id not in _pending:
            rep = await rich_send(
                bot, chat_id,
                rich_heading("❍ ᴄᴏᴏʟᴅᴏᴡɴ ᴀᴄᴛɪᴠᴇ", level=3)
                + rich_kv_table([("ᴘʀᴏᴄᴇssɪɴɢ ɪɴ", f"<code>{rem}s</code>")]),
            )
            _pending[chat_id] = (message, rep)
            asyncio.create_task(_run_pending(chat_id, rem))
        return

    _last_cmd[chat_id] = now

    if not query:
        await rich_send(
            bot, chat_id,
            rich_heading("❍ ᴜsᴀɢᴇ", level=3)
            + rich_kv_table([
                ("ᴘʟᴀʏ", "<code>/play song name</code>"),
                ("ᴏʀ", "<code>/play youtube url</code>"),
                ("ᴠɪᴅᴇᴏ", "<code>/vplay song name</code>"),
            ]),
        )
        return

    await _process_play(message, query, video=(cmd == "vplay"))


# ── Process play ───────────────────────────────────────────────────────────────

async def _process_play(message: Message, query: str, video: bool = False) -> None:
    chat_id = message.chat.id

    pm = await rich_send(bot, chat_id, rich_heading("❍ ᴘʀᴏᴄᴇssɪɴɢ...", level=3))

    # Assistant check — uses utils/assistant.py
    status = await is_assistant_in(chat_id)

    if status == "banned":
        await rich_edit(
            pm,
            rich_heading("❍ ᴀssɪsᴛᴀɴᴛ ʙᴀɴɴᴇᴅ", level=3)
            + rich_note("ᴘʟᴇᴀsᴇ ᴜɴʙᴀɴ ᴀssɪsᴛᴀɴᴛ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ"),
        )
        return

    if not status:
        await rich_edit(pm, rich_heading("❍ ᴀssɪsᴛᴀɴᴛ ɪs ᴊᴏɪɴɪɴɢ ᴛʜᴇ ɢʀᴏᴜᴘ...", level=3))
        ok = await try_join_assistant(chat_id, pm)
        if not ok:
            return
        await rich_edit(
            pm,
            rich_heading("❍ ᴀssɪsᴛᴀɴᴛ ʜᴀs ᴊᴏɪɴᴇᴅ ✓", level=3)
            + rich_note("ᴘʀᴏᴄᴇssɪɴɢ..."),
        )

    # Normalise short YouTube URL
    if "youtu.be" in query:
        m = re.search(r"youtu\.be/([^?&]+)", query)
        if m:
            query = f"https://www.youtube.com/watch?v={m.group(1)}"

    # Search YouTube
    try:
        result = await search_yt(query)
    except Exception as e:
        await rich_edit(
            pm,
            rich_heading("❍ sᴇᴀʀᴄʜ ғᴀɪʟᴇᴅ", level=3)
            + rich_note(f"<code>{rich_esc(e)}</code>"),
        )
        return

    # Playlist
    if isinstance(result, dict) and "playlist" in result:
        items = result["playlist"]
        if not items:
            await rich_edit(pm, rich_heading("❍ ᴘʟᴀʏʟɪsᴛ ᴇᴍᴘᴛʏ", level=3))
            return

        req    = message.from_user.first_name if message.from_user else "Unknown"
        req_id = message.from_user.id         if message.from_user else 0

        first_was_empty = queue_size(chat_id) == 0

        for item in items:
            add_to_queue(chat_id, {
                "url":              item["link"],
                "title":            item["title"],
                "duration":         iso_to_human(item["duration"]),
                "duration_seconds": iso_to_sec(item["duration"]),
                "requester":        req,
                "requester_id":     req_id,
                "thumbnail":        item["thumbnail"],
            })

        rows = [
            ("sᴏɴɢs", f"<code>{len(items)}</code>"),
            ("ғɪʀsᴛ", f"<code>{rich_esc(short(items[0]['title']))}</code>"),
        ]
        if len(items) > 1:
            rows.append(("ɴᴇxᴛ", f"<code>{rich_esc(short(items[1]['title']))}</code>"))

        await rich_send(
            bot, chat_id,
            rich_heading("❍ ᴘʟᴀʏʟɪsᴛ ᴀᴅᴅᴇᴅ", level=3) + rich_kv_table(rows),
        )

        if first_was_empty:
            first_song = peek_current(chat_id)
            if first_song:
                await play_song(chat_id, pm, first_song)
        else:
            await pm.delete()
        return

    # Single track
    url, title, dur_iso, thumb = result

    if not url:
        await rich_edit(pm, rich_heading("❍ sᴏɴɢ ɴᴏᴛ ғᴏᴜɴᴅ", level=3))
        return

    secs = iso_to_sec(dur_iso)

    if secs > config.MAX_DURATION_SECONDS:
        await rich_edit(
            pm,
            rich_heading("❍ sᴏɴɢ ᴛᴏᴏ ʟᴏɴɢ", level=3)
            + rich_kv_table([
                ("ᴅᴜʀ", f"<code>{iso_to_human(dur_iso)}</code>"),
                ("ᴍᴀx", f"<code>{config.MAX_DURATION_SECONDS // 60} min</code>"),
            ]),
        )
        return

    req    = message.from_user.first_name if message.from_user else "Unknown"
    req_id = message.from_user.id         if message.from_user else 0

    song = {
        "url":              url,
        "title":            title,
        "duration":         iso_to_human(dur_iso),
        "duration_seconds": secs,
        "requester":        req,
        "requester_id":     req_id,
        "thumbnail":        thumb,
        "video":            video,
    }

    pos = add_to_queue(chat_id, song)

    if pos == 1:
        await play_song(chat_id, pm, song)
    else:
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("⌯ sᴋɪᴘ ⌯",  callback_data="skip"),
            InlineKeyboardButton("⌯ ᴄʟᴇᴀʀ ⌯", callback_data="clear"),
        ]])
        await rich_send(
            bot, chat_id,
            rich_heading("❍ ᴀᴅᴅᴇᴅ ᴛᴏ ǫᴜᴇᴜᴇ", level=3)
            + rich_kv_table([
                ("ᴛɪᴛʟᴇ", f"<code>{rich_esc(short(title))}</code>"),
                ("ᴅᴜʀ", f"<code>{iso_to_human(dur_iso)}</code>"),
                ("ʙʏ", f"<code>{rich_esc(req)}</code>"),
                ("ᴘᴏs", f"<code>#{pos - 1}</code>"),
            ]),
            reply_markup=kb,
        )
        await pm.delete()
        

# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import time

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from ShizuMusic import bot, call_py, LOGGER
from ShizuMusic.core.queue import peek_current
from ShizuMusic.modules.block import group_allowed, user_allowed
from ShizuMusic.utils.formatters import fmt_time, parse_dur, progress_bar, short
from ShizuMusic.utils.rich_ui import (
    rich_edit,
    rich_esc,
    rich_heading,
    rich_img,
    rich_kv_table,
    rich_note,
    rich_send,
)
from ShizuMusic.utils.youtube import resolve_stream

# ── Seek state tracker ─────────────────────────────────────────────────────────
_seek_state: dict[int, dict] = {}


def set_seek_state(chat_id: int, offset: int) -> None:
    _seek_state[chat_id] = {"start_ts": time.time(), "offset": offset}


def get_current_position(chat_id: int) -> int:
    state = _seek_state.get(chat_id)
    if not state:
        return 0
    return state["offset"] + int(time.time() - state["start_ts"])


def clear_seek_state(chat_id: int) -> None:
    _seek_state.pop(chat_id, None)


# ── Internal seek ──────────────────────────────────────────────────────────────

async def _seek_to(chat_id: int, target_sec: int, message: Message) -> None:
    from pytgcalls.types import AudioQuality, MediaStream

    song = peek_current(chat_id)
    if not song:
        await rich_send(bot, chat_id, rich_heading("❍ ɴᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ ʀɪɢʜᴛ ɴᴏᴡ", level=3))
        return

    total_sec  = parse_dur(song.get("duration", "0:00"))
    target_sec = max(0, min(target_sec, total_sec - 1))

    pm = await rich_send(
        bot, chat_id,
        rich_heading("⏩ sᴇᴇᴋɪɴɢ...", level=3)
        + rich_kv_table([("ᴛᴏ", f"<code>{fmt_time(target_sec)}</code>")]),
    )

    try:
        media_path = await resolve_stream(song["url"])
    except Exception as e:
        await rich_edit(
            pm,
            rich_heading("❍ sᴇᴇᴋ ғᴀɪʟᴇᴅ — ᴄᴏᴜʟᴅ ɴᴏᴛ ʀᴇsᴏʟᴠᴇ sᴛʀᴇᴀᴍ", level=3)
            + rich_note(f"<code>{rich_esc(e)}</code>"),
        )
        return

    try:
        await call_py.change_stream(
            chat_id,
            MediaStream(
                media_path,
                audio_parameters=AudioQuality.HIGH,
                video_flags=MediaStream.Flags.IGNORE,
                ffmpeg_parameters=f"-ss {target_sec}",
            ),
        )
    except Exception:
        try:
            await call_py.play(
                chat_id,
                MediaStream(
                    media_path,
                    audio_parameters=AudioQuality.HIGH,
                    video_flags=MediaStream.Flags.IGNORE,
                    ffmpeg_parameters=f"-ss {target_sec}",
                ),
            )
        except Exception as e2:
            await rich_edit(
                pm,
                rich_heading("❍ sᴇᴇᴋ ғᴀɪʟᴇᴅ", level=3)
                + rich_note(f"<code>{rich_esc(e2)}</code>"),
            )
            return

    set_seek_state(chat_id, target_sec)

    # True rich card — same pattern as the now-playing message in player.py
    # (embedded thumbnail via rich_img, real heading + table), not a caption.
    content = (
        rich_heading("🎧 sʜɪᴢᴜ ᴍᴜsɪᴄ — ɴᴏᴡ ᴘʟᴀʏɪɴɢ", level=3)
        + (rich_img(song["thumbnail"]) if song.get("thumbnail") else "")
        + rich_kv_table([
            ("ᴛɪᴛʟᴇ", rich_esc(short(song["title"]))),
            ("ᴅᴜʀᴀᴛɪᴏɴ", rich_esc(song.get("duration", "?"))),
            ("ʙʏ", rich_esc(song["requester"])),
            ("sᴇᴇᴋᴇᴅ ᴛᴏ", f"<code>{fmt_time(target_sec)}</code>"),
        ])
    )
    btns = [
        InlineKeyboardButton("▷",   callback_data="resume"),
        InlineKeyboardButton("II",  callback_data="pause"),
        InlineKeyboardButton("‣‣I", callback_data="skip"),
        InlineKeyboardButton("▢",   callback_data="stop"),
    ]
    bar = progress_bar(target_sec, total_sec)
    kb  = InlineKeyboardMarkup([
        [InlineKeyboardButton(bar, callback_data="noop")],
        btns,
    ])
    try:
        await pm.delete()
    except Exception:
        pass
    await rich_send(bot, chat_id, content, reply_markup=kb)


# ── /seek ──────────────────────────────────────────────────────────────────────

@bot.on_message(
    filters.group
    & filters.regex(r"^/seek(?:@\w+)?\s+(?P<sec>\d+)$")
    & group_allowed
    & user_allowed
)
async def seek_cmd(_, message: Message) -> None:
    chat_id = message.chat.id
    song    = peek_current(chat_id)

    if not song:
        await rich_send(bot, chat_id, rich_heading("❍ ɴᴏ sᴏɴɢ ɪs ᴄᴜʀʀᴇɴᴛʟʏ ᴘʟᴀʏɪɴɢ", level=3))
        return

    sec = int(message.matches[0].group("sec"))
    if sec < 1:
        await rich_send(
            bot, chat_id,
            rich_heading("❍ ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ɴᴜᴍʙᴇʀ ᴏғ sᴇᴄᴏɴᴅs ɢʀᴇᴀᴛᴇʀ ᴛʜᴀɴ 0", level=3)
            + rich_kv_table([("ᴜsᴀɢᴇ", "<code>/seek 30</code>")]),
        )
        return

    current_pos = get_current_position(chat_id)
    target      = current_pos + sec
    total_sec   = parse_dur(song.get("duration", "0:00"))

    if current_pos >= total_sec - 1:
        await rich_send(bot, chat_id, rich_heading("❍ sᴏɴɢ ɪs ᴀʟᴍᴏsᴛ ғɪɴɪsʜᴇᴅ, ᴄᴀɴɴᴏᴛ sᴇᴇᴋ ғᴏʀᴡᴀʀᴅ", level=3))
        return

    if target >= total_sec:
        await rich_send(
            bot, chat_id,
            rich_heading("❍ ᴄᴀɴɴᴏᴛ sᴇᴇᴋ ᴛʜᴀᴛ ғᴀʀ ғᴏʀᴡᴀʀᴅ", level=3)
            + rich_kv_table([
                ("ᴄᴜʀʀᴇɴᴛ ᴘᴏsɪᴛɪᴏɴ", f"<code>{fmt_time(current_pos)}</code>"),
                ("sᴏɴɢ ᴅᴜʀᴀᴛɪᴏɴ", f"<code>{fmt_time(total_sec)}</code>"),
            ]),
        )
        return

    try:
        await message.delete()
    except Exception:
        pass

    await _seek_to(chat_id, target, message)


# ── /seekback ──────────────────────────────────────────────────────────────────

@bot.on_message(
    filters.group
    & filters.regex(r"^/seekback(?:@\w+)?\s+(?P<sec>\d+)$")
    & group_allowed
    & user_allowed
)
async def seekback_cmd(_, message: Message) -> None:
    chat_id = message.chat.id
    song    = peek_current(chat_id)

    if not song:
        await rich_send(bot, chat_id, rich_heading("❍ ɴᴏ sᴏɴɢ ɪs ᴄᴜʀʀᴇɴᴛʟʏ ᴘʟᴀʏɪɴɢ", level=3))
        return

    sec = int(message.matches[0].group("sec"))
    if sec < 1:
        await rich_send(
            bot, chat_id,
            rich_heading("❍ ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ɴᴜᴍʙᴇʀ ᴏғ sᴇᴄᴏɴᴅs ɢʀᴇᴀᴛᴇʀ ᴛʜᴀɴ 0", level=3)
            + rich_kv_table([("ᴜsᴀɢᴇ", "<code>/seekback 30</code>")]),
        )
        return

    target = max(0, get_current_position(chat_id) - sec)

    try:
        await message.delete()
    except Exception:
        pass

    await _seek_to(chat_id, target, message)


# ── /seek (no args) ────────────────────────────────────────────────────────────

@bot.on_message(
    filters.group
    & filters.regex(r"^/seek(?:@\w+)?$")
    & group_allowed
    & user_allowed
)
async def seek_usage(_, message: Message) -> None:
    chat_id = message.chat.id
    song    = peek_current(chat_id)

    usage_rows = [
        ("/seek 30", "ғᴏʀᴡᴀʀᴅ 30 sᴇᴄᴏɴᴅs"),
        ("/seekback 30", "ʙᴀᴄᴋᴡᴀʀᴅ 30 sᴇᴄᴏɴᴅs"),
    ]

    if song:
        pos       = get_current_position(chat_id)
        total_sec = parse_dur(song.get("duration", "0:00"))
        await rich_send(
            bot, chat_id,
            rich_heading("❍ sᴇᴇᴋ ᴜsᴀɢᴇ", level=3)
            + rich_kv_table([("ᴄᴜʀʀᴇɴᴛ ᴘᴏsɪᴛɪᴏɴ",
                              f"<code>{fmt_time(pos)}</code> / <code>{fmt_time(total_sec)}</code>")])
            + rich_kv_table(usage_rows, headers=["ᴄᴏᴍᴍᴀɴᴅ", "ᴅᴇsᴄʀɪᴘᴛɪᴏɴ"]),
        )
    else:
        await rich_send(
            bot, chat_id,
            rich_heading("❍ sᴇᴇᴋ ᴜsᴀɢᴇ", level=3)
            + rich_kv_table(usage_rows, headers=["ᴄᴏᴍᴍᴀɴᴅ", "ᴅᴇsᴄʀɪᴘᴛɪᴏɴ"]),
        )


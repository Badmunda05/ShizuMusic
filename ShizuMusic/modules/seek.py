# ═══════════════════════════════════════════════════════════════
#                     🎵 SHIZUMUSIC
#
#                   © 2026 BAD MUNDA
#
#                Developed with ❤️ by Bad Munda
#
#             Do not remove or alter the original credits.
#
#           Copyright © 2026 Bad Munda. All rights reserved.
#
#              
# ═══════════════════════════════════════════════════════════════

import time

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from ShizuMusic import bot, call_py, LOGGER
from ShizuMusic.core.channels import target_chat
from ShizuMusic.core.queue import peek_current
from ShizuMusic.modules.block import group_allowed, user_allowed
from ShizuMusic.utils.buttons import player_controls_kb
from ShizuMusic.utils.db import is_thumbnail_enabled
from ShizuMusic.utils.thumbnail import thumbnail_html
from ShizuMusic.utils.formatters import fmt_time, parse_dur, short
from ShizuMusic.utils.language import chat_strings
from richgram import (
    rich_edit,
    rich_esc,
    rich_heading,
    rich_img,
    rich_kv_table,
    rich_note,
    rich_send,
)
from ShizuMusic.utils.youtube import resolve_stream, resolve_video_stream

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
    from pytgcalls.types import AudioQuality, MediaStream, VideoQuality

    lang = chat_strings(chat_id)

    song = peek_current(chat_id)
    if not song:
        await rich_send(bot, chat_id, rich_heading(lang["seek_no_song_title"], level=3))
        return

    total_sec  = parse_dur(song.get("duration", "0:00"))
    target_sec = max(0, min(target_sec, total_sec - 1))

    pm = await rich_send(
        bot, chat_id,
        rich_heading(lang["seek_seeking_title"], level=3)
        + rich_kv_table([(lang["kv_to"], f"<code>{fmt_time(target_sec)}</code>")]),
    )

    is_video = song.get("video", False)

    if is_video:
        stream_kwargs = dict(
            audio_parameters=AudioQuality.HIGH,
            video_parameters=VideoQuality.HD_720p,
            ffmpeg_parameters=f"-ss {target_sec}",
        )
    else:
        stream_kwargs = dict(
            audio_parameters=AudioQuality.HIGH,
            video_flags=MediaStream.Flags.IGNORE,
            ffmpeg_parameters=f"-ss {target_sec}",
        )

    try:
        if is_video:
            media_path = await resolve_video_stream(song["url"])
        else:
            media_path = await resolve_stream(song["url"])
    except Exception as e:
        await rich_edit(
            pm,
            rich_heading(lang["seek_failed_resolve_title"], level=3)
            + rich_note(f"<code>{rich_esc(e)}</code>"),
        )
        return

    try:
        await call_py.change_stream(
            chat_id,
            MediaStream(media_path, **stream_kwargs),
        )
    except Exception:
        try:
            await call_py.play(
                chat_id,
                MediaStream(media_path, **stream_kwargs),
            )
        except Exception as e2:
            await rich_edit(
                pm,
                rich_heading(lang["seek_failed_title"], level=3)
                + rich_note(f"<code>{rich_esc(e2)}</code>"),
            )
            return

    set_seek_state(chat_id, target_sec)

    # True rich card — same pattern as the now-playing message in player.py
    # (embedded thumbnail via rich_img, real heading + table), not a caption.
    content = (
        rich_heading(lang["now_playing_title"], level=3)
        + thumbnail_html(song, is_thumbnail_enabled(chat_id))      # utils/thumbnail.py
        + rich_kv_table([
            (lang["kv_title"], rich_esc(short(song["title"]))),
            (lang["kv_duration"], rich_esc(song.get("duration", "?"))),
            (lang["kv_by"], rich_esc(song["requester"])),
            (lang["kv_seeked_to"], f"<code>{fmt_time(target_sec)}</code>"),
        ])
    )
    kb = player_controls_kb(target_sec, total_sec, chat_id, lang)
    try:
        await pm.delete()
    except Exception:
        pass
    await rich_send(bot, chat_id, content + kb)


# ── /seek ──────────────────────────────────────────────────────────────────────

@bot.on_message(
    filters.group
    & filters.regex(r"^/c?seek(?:@\w+)?\s+(?P<sec>\d+)$")
    & group_allowed
    & user_allowed
)
async def seek_cmd(_, message: Message) -> None:
    chat_id = await target_chat(message)
    if chat_id is None:
        return
    lang = chat_strings(chat_id)
    song    = peek_current(chat_id)

    if not song:
        await rich_send(bot, chat_id, rich_heading(lang["seek_no_song_title"], level=3))
        return

    sec = int(message.matches[0].group("sec"))
    if sec < 1:
        await rich_send(
            bot, chat_id,
            rich_heading(lang["seek_invalid_seconds_title"], level=3)
            + rich_kv_table([(lang["kv_usage"], "<code>/seek 30</code>")]),
        )
        return

    current_pos = get_current_position(chat_id)
    target      = current_pos + sec
    total_sec   = parse_dur(song.get("duration", "0:00"))

    if current_pos >= total_sec - 1:
        await rich_send(bot, chat_id, rich_heading(lang["seek_almost_finished_title"], level=3))
        return

    if target >= total_sec:
        await rich_send(
            bot, chat_id,
            rich_heading(lang["seek_too_far_title"], level=3)
            + rich_kv_table([
                (lang["kv_current_position"], f"<code>{fmt_time(current_pos)}</code>"),
                (lang["kv_song_duration"], f"<code>{fmt_time(total_sec)}</code>"),
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
    & filters.regex(r"^/c?seekback(?:@\w+)?\s+(?P<sec>\d+)$")
    & group_allowed
    & user_allowed
)
async def seekback_cmd(_, message: Message) -> None:
    chat_id = await target_chat(message)
    if chat_id is None:
        return
    lang = chat_strings(chat_id)
    song    = peek_current(chat_id)

    if not song:
        await rich_send(bot, chat_id, rich_heading(lang["seek_no_song_title"], level=3))
        return

    sec = int(message.matches[0].group("sec"))
    if sec < 1:
        await rich_send(
            bot, chat_id,
            rich_heading(lang["seek_invalid_seconds_title"], level=3)
            + rich_kv_table([(lang["kv_usage"], "<code>/seekback 30</code>")]),
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
    & filters.regex(r"^/c?seek(?:@\w+)?$")
    & group_allowed
    & user_allowed
)
async def seek_usage(_, message: Message) -> None:
    chat_id = await target_chat(message)
    if chat_id is None:
        return
    lang = chat_strings(chat_id)
    song    = peek_current(chat_id)

    usage_rows = lang["seek_usage_rows"]

    if song:
        pos       = get_current_position(chat_id)
        total_sec = parse_dur(song.get("duration", "0:00"))
        await rich_send(
            bot, chat_id,
            rich_heading(lang["seek_usage_title"], level=3)
            + rich_kv_table([(lang["kv_current_position"],
                              f"<code>{fmt_time(pos)}</code> / <code>{fmt_time(total_sec)}</code>")])
            + rich_kv_table(usage_rows, headers=[lang["kv_command"], lang["kv_description"]]),
        )
    else:
        await rich_send(
            bot, chat_id,
            rich_heading(lang["seek_usage_title"], level=3)
            + rich_kv_table(usage_rows, headers=[lang["kv_command"], lang["kv_description"]]),
        )
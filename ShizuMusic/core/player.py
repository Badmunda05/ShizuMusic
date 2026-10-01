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

import asyncio
import random
import time

from pyrogram.enums import ParseMode
from pyrogram.raw.functions.phone import CreateGroupCall
from pyrogram.types import Message

from pytgcalls import PyTgCalls
from pytgcalls import filters as fl
from ntgcalls import TelegramServerError
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.types import (
    AudioQuality,
    MediaStream,
    VideoQuality,
    ChatUpdate,
    StreamEnded,
    GroupCallConfig,
    GroupCallParticipant,
    UpdatedGroupCallParticipant,
)

import config

from ShizuMusic import (
    LOGGER,
    assistant,
    bot,
    call_py,
)

from ShizuMusic.core.queue import (
    remove_from_queue,
)

from ShizuMusic.strings import DEFAULT_LANG, get_string
from ShizuMusic.utils.buttons import player_controls_kb, support_updates_pills
from ShizuMusic.utils.db import is_thumbnail_enabled

from ShizuMusic.utils.formatters import (
    parse_dur,
    progress_bar,
    short,
)

from ShizuMusic.utils.language import chat_strings
from ShizuMusic.utils.logs import logger_active
from ShizuMusic.utils.routes import notify_chat, register_panel
from ShizuMusic.utils.thumbnail import thumbnail_html

from richgram import (
    rich_edit,
    rich_esc,
    rich_heading,
    rich_img,
    rich_kv_table,
    rich_note,
    rich_send,
)

from ShizuMusic.utils.youtube import (
    resolve_stream,
    resolve_video_stream,
)

# ─────────────────────────────────────────────
# NOW PLAYING CONTENT
# ─────────────────────────────────────────────


def _now_playing_content(song: dict, lang: dict, show_thumb: bool = True) -> str:
    """Now-playing rich message content (thumbnail only if the chat has it ON)."""

    return (
        rich_heading(
            lang["now_playing_title"],
            level=3
        )
        + thumbnail_html(song, show_thumb)      # picture comes from utils/thumbnail.py
        + rich_kv_table([
            (lang["kv_title"], rich_esc(short(song["title"]))),
            (lang["kv_duration"], rich_esc(song.get("duration", "?"))),
            (lang["kv_by"], rich_esc(song["requester"])),
        ])
        + support_updates_pills(lang)
    )


def _now_playing_kb(elapsed: float, total: float, chat_id=None, lang=None) -> str:
    """Player buttons as rich HTML — append to the message content."""
    return player_controls_kb(elapsed, total, chat_id, lang)


_panel_content: dict = {}


def get_panel_content(chat_id: int, message_id: int):
    return _panel_content.get((chat_id, message_id))


# ─────────────────────────────────────────────
# PROGRESS UPDATER
# ─────────────────────────────────────────────


_closed_panels: set = set()


def mark_panel_closed(chat_id: int, message_id: int) -> None:
    _closed_panels.add((chat_id, message_id))
    _panel_content.pop((chat_id, message_id), None)


async def _update_progress(
    chat_id: int,
    msg: Message,
    start_t: float,
    total: float,
    content: str,
) -> None:

    while True:

        if (chat_id, msg.id) in _closed_panels:
            _closed_panels.discard((chat_id, msg.id))
            break

        elapsed = min(time.time() - start_t, total)
        kb = _now_playing_kb(elapsed, total, chat_id, chat_strings(chat_id))

        try:
            await rich_edit(msg, content + kb)

        except Exception as e:
            if "MESSAGE_NOT_MODIFIED" not in str(e):
                break

        if elapsed >= total:
            break

        await asyncio.sleep(18)


# ─────────────────────────────────────────────
# AUTO START VC
# ─────────────────────────────────────────────

async def _ensure_vc(chat_id: int) -> bool:

    lang = chat_strings(chat_id)

    try:

        chat_id = int(chat_id)
        chat = await assistant.get_chat(chat_id)

        await assistant.invoke(
            CreateGroupCall(
                peer=await assistant.resolve_peer(chat.id),
                random_id=random.randint(10000, 99999),
            )
        )

        LOGGER.info(f"[VC] Created in {chat_id}")
        await asyncio.sleep(2)
        return True

    except TelegramServerError as e:
        LOGGER.error(f"[VC] TelegramServerError: {e}")
        await rich_send(
            bot, chat_id,
            rich_heading(lang["vc_start_failed_server_title"], level=3)
            + rich_note(f"<code>{rich_esc(e)}</code>"),
        )
        return False

    except Exception as e:

        err = str(e).lower()

        # already active
        if "already" in err or "groupcall_already_started" in err:
            return True

        # admin rights missing
        if "chat_admin_required" in err or "admin" in err:
            await rich_send(
                bot, chat_id,
                rich_heading(lang["vc_perm_missing_title"], level=3)
                + rich_note(lang["vc_perm_missing_note"]),
            )
            return False

        LOGGER.error(f"[VC ERROR] {e}")
        await rich_send(
            bot, chat_id,
            rich_heading(lang["vc_start_failed_title"], level=3)
            + rich_note(f"<code>{rich_esc(e)}</code>"),
        )
        return False


# ─────────────────────────────────────────────
# MAIN PLAY FUNCTION
# ─────────────────────────────────────────────

async def play_song(
    chat_id: int,
    message: Message,
    song: dict,
) -> None:

    chat_id = int(chat_id)
    lang = chat_strings(chat_id)
    url = song.get("url")

    if not url:
        return

    loading_text = (
        rich_heading(lang["loading_title"], level=3)
        + rich_kv_table([(lang["kv_song"], rich_esc(short(song['title'])))])
    )

    try:
        await rich_edit(message, loading_text)

    except Exception:
        message = await rich_send(bot, chat_id, loading_text)

    # ─────────────────────────────────────────
    # RESOLVE STREAM
    # ─────────────────────────────────────────

    is_video = song.get("video", False)

    try:
        if is_video:
            media_path = await resolve_video_stream(url)
        else:
            media_path = await resolve_stream(url)

    except Exception as e:
        try:
            remove_from_queue(chat_id, 0)
        except Exception:
            pass

        await rich_send(
            bot, chat_id,
            rich_heading(lang["download_failed_title"], level=3)
            + rich_note(f"<code>{rich_esc(e)}</code>"),
        )
        return

    # ─────────────────────────────────────────
    # AUTO EFFECTS
    # ─────────────────────────────────────────

    if not is_video:
        try:
            from ShizuMusic.modules.effects import maybe_apply_effects
            media_path = await maybe_apply_effects(chat_id, media_path)

        except Exception as fx_err:
            LOGGER.warning(f"[Effects] Skipped: {fx_err}")

    # ─────────────────────────────────────────
    # PLAY STREAM
    # ─────────────────────────────────────────

    played = False

    for attempt in range(2):

        try:

            if is_video:
                await call_py.play(
                    chat_id,
                    MediaStream(
                        media_path,
                        audio_parameters=AudioQuality.HIGH,
                        video_parameters=VideoQuality.HD_720p,
                    ),
                )
            else:
                await call_py.play(
                    chat_id,
                    MediaStream(
                        media_path,
                        audio_parameters=AudioQuality.HIGH,
                        video_flags=MediaStream.Flags.IGNORE,
                    ),
                )

            played = True
            break

        except NoActiveGroupCall:

            if attempt == 0:
                LOGGER.info(f"[VC] NoActiveGroupCall — Creating VC in {chat_id}")
                ok = await _ensure_vc(chat_id)

                if ok:
                    continue

                try:
                    remove_from_queue(chat_id, 0)
                except Exception:
                    pass

                return

        except TelegramServerError as e:
            LOGGER.error(f"[PLAY] TelegramServerError: {e}")

            try:
                remove_from_queue(chat_id, 0)
            except Exception:
                pass

            await rich_send(
                bot, chat_id,
                rich_heading(lang["playback_failed_server_title"], level=3)
                + rich_note(f"<code>{rich_esc(e)}</code>"),
            )
            return

        except Exception as e:

            err = str(e).lower()

            vc_missing = any(
                x in err
                for x in (
                    "groupcallnotfound",
                    "not_in_group_call",
                    "groupcall_forbidden",
                    "not in group call",
                    "no active group call",
                )
            )

            # auto create vc (string-based fallback)
            if vc_missing and attempt == 0:
                LOGGER.info(f"[VC] Creating VC in {chat_id}")
                ok = await _ensure_vc(chat_id)

                if ok:
                    continue

                try:
                    remove_from_queue(chat_id, 0)
                except Exception:
                    pass

                return

            # admin permission error
            if "chat_admin_required" in err or "admin" in err:
                try:
                    remove_from_queue(chat_id, 0)
                except Exception:
                    pass

                await rich_send(
                    bot, chat_id,
                    rich_heading(lang["vc_perm_missing_title"], level=3)
                    + rich_note(lang["playback_perm_missing_note"]),
                )
                LOGGER.error(f"[ADMIN ERROR] {e}")
                return

            # generic error
            try:
                remove_from_queue(chat_id, 0)
            except Exception:
                pass

            await rich_send(
                bot, chat_id,
                rich_heading(lang["effects_playback_failed_title"], level=3)
                + rich_note(f"<code>{rich_esc(e)}</code>"),
            )
            LOGGER.error(f"[PLAY ERROR] {e}")
            return

    if not played:
        return

    try:
        from ShizuMusic.core.autoplay import schedule_prefetch
        schedule_prefetch(chat_id, song)
    except Exception:
        pass

    # ─────────────────────────────────────────
    # RESET SEEK
    # ─────────────────────────────────────────

    try:
        from ShizuMusic.modules.seek import set_seek_state
        set_seek_state(chat_id, 0)
    except Exception:
        pass

    # ─────────────────────────────────────────
    # DATABASE TRACKING
    # ─────────────────────────────────────────

    try:
        from ShizuMusic.database import (
            add_served_chat,
            add_served_user,
            increment_play_count,
        )

        add_served_chat(notify_chat(chat_id))      # never put a channel in the broadcast list
        requester_id = song.get("requester_id")

        if requester_id:
            add_served_user(requester_id)

        increment_play_count(chat_id)

    except Exception as db_err:
        LOGGER.warning(f"[DB ERROR] {db_err}")



    total = parse_dur(song.get("duration", "0:00"))
    content = _now_playing_content(song, lang, is_thumbnail_enabled(chat_id))
    kb = _now_playing_kb(0, total, chat_id, lang)

    try:
        pmsg = await rich_edit(message, content + kb)
        if pmsg is None:
            pmsg = message
    except Exception:
        pmsg = await rich_send(bot, chat_id, content + kb)

    _panel_content[(chat_id, pmsg.id)] = content
    # channel play: the panel lives in the group but its buttons drive the channel VC
    register_panel(pmsg.chat.id, pmsg.id, chat_id)

    asyncio.create_task(
        _update_progress(
            chat_id,
            pmsg,
            time.time(),
            total,
            content,
        )
    )

    # ─────────────────────────────────────────
    # LOGGER
    # ─────────────────────────────────────────

    if logger_active():
        en = get_string(DEFAULT_LANG)
        logger_content = (
            rich_heading(en["logger_nowplaying_title"], level=3)
            + rich_kv_table([
                (en["kv_title"], rich_esc(song.get("title", "?"))),
                (en["kv_duration"], rich_esc(song.get("duration", "?"))),
                (en["kv_by"], rich_esc(song.get("requester", "?"))),
                (en["kv_chat_name"], rich_esc(await _chat_name(chat_id, message))),
                (en["kv_chat_id"], f"<code>{chat_id}</code>"),
            ])
        )

        asyncio.create_task(
            rich_send(
                bot,
                config.LOGGER_ID,
                logger_content,
            )
        )


async def _chat_name(chat_id: int, message=None) -> str:
    """Best-effort chat title for the log message (group title / user's name)."""
    chat = getattr(message, "chat", None)
    name = getattr(chat, "title", None) or getattr(chat, "first_name", None)
    # channel play: the panel message sits in the group, but the log should name the channel
    if name and getattr(chat, "id", chat_id) == chat_id:
        return str(name)
    try:
        chat = await bot.get_chat(chat_id)
        return str(getattr(chat, "title", None) or getattr(chat, "first_name", None) or chat_id)
    except Exception:
        return str(chat_id)
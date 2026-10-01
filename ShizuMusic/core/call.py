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

from pytgcalls import filters as fl
from ntgcalls import TelegramServerError
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.types import (
    ChatUpdate,
    StreamEnded,
)

from ShizuMusic import LOGGER, bot, call_py
from ShizuMusic.core.queue import clear_queue, peek_current, pop_current, queue_size
from ShizuMusic.utils.helpers import delete_file
from ShizuMusic.utils.language import chat_strings
from richgram import rich_esc, rich_heading, rich_kv_table, rich_note, rich_send


async def leave_vc(chat_id: int) -> None:
    """
    Leave voice chat and clean the queue (AutoPlay's ON/OFF setting is kept).
    """

    # Drop pending autoplay suggestions, but keep the ON/OFF setting: once
    # an admin turns AutoPlay on it stays on until they turn it off.
    try:
        from ShizuMusic.core.autoplay import reset_autoplay_state
        reset_autoplay_state(chat_id)
    except Exception:
        pass

    # Delete queued files
    for song in clear_queue(chat_id):
        try:
            delete_file(song.get("file_path", ""))
        except Exception:
            pass

    try:
        await call_py.leave_call(chat_id)

    except NoActiveGroupCall:
        pass

    except TelegramServerError as e:
        LOGGER.error(f"Leave VC TelegramServerError: {e}")

    except Exception as e:
        LOGGER.error(f"Leave VC Error: {e}")


@call_py.on_update(fl.chat_update(ChatUpdate.Status.LEFT_CALL))
async def on_call_left(_: object, update: ChatUpdate) -> None:
    """
    The voice chat ended from OUTSIDE our own leave_vc() flow — someone
    ended it from Telegram's UI, the assistant got kicked, Telegram
    dropped the call, etc. (KICKED / LEFT_GROUP / CLOSED_VOICE_CHAT /
    DISCARDED_CALL / BUSY_CALL — see pytgcalls' ChatUpdate.Status).

    No stream is left to ever fire `stream_end` for, so without this the
    queue keeps thinking a song is still "playing": /play just appends
    behind that ghost entry and nothing plays again until the bot is
    restarted. Clearing state here means the next /play starts clean.
    """

    chat_id = update.chat_id
    LOGGER.warning(f"[VC] Call ended externally in {chat_id} ({update.status}) — clearing state")

    for song in clear_queue(chat_id):
        try:
            delete_file(song.get("file_path", ""))
        except Exception:
            pass

    try:
        from ShizuMusic.core.autoplay import reset_autoplay_state
        reset_autoplay_state(chat_id)
    except Exception:
        pass

    try:
        lang = chat_strings(chat_id)
        await rich_send(
            bot, chat_id,
            rich_heading(lang["vc_ended_title"], level=3)
            + rich_note(lang["vc_ended_note"]),
        )
    except Exception:
        pass


@call_py.on_update(fl.stream_end())
async def on_stream_end(_: object, update: StreamEnded) -> None:
    """
    Automatically play the next song when the current stream ends.
    If the queue is empty, AutoPlay (when ON) adds one related song
    before we give up and leave the voice chat.
    """

    chat_id = update.chat_id
    lang = chat_strings(chat_id)

    # Remove finished song
    done = pop_current(chat_id)

    if done:
        await asyncio.sleep(1)

        try:
            delete_file(done.get("file_path", ""))

        except Exception:
            pass

    nxt = peek_current(chat_id)

    # ── Queue is empty: let AutoPlay try to add ONE related song ────────────────
    if not nxt:
        try:
            from ShizuMusic.core.autoplay import autoplay_next

            if await autoplay_next(chat_id, done):
                nxt = peek_current(chat_id)

        except Exception as ap_err:
            LOGGER.warning(f"[AutoPlay] autoplay_next error: {ap_err}")

    # ── Play next song ───────────────────────────────────────────────────────
    if nxt:

        from ShizuMusic.core.player import play_song

        # start getting the *next* suggestion ready while this song plays
        try:
            from ShizuMusic.core.autoplay import schedule_prefetch
            schedule_prefetch(chat_id, nxt)
        except Exception:
            pass

        try:
            msg = await rich_send(
                bot, chat_id,
                rich_heading(lang["next_track_title"], level=3)
                + rich_kv_table([(lang["kv_title"], f"<code>{rich_esc(nxt['title'])}</code>")]),
            )

            await play_song(chat_id, msg, nxt)

        except (NoActiveGroupCall, TelegramServerError) as e:
            LOGGER.error(f"Next Song VC Error: {e}")

        except Exception as e:
            LOGGER.error(f"Next Song Error: {e}")

            await rich_send(
                bot, chat_id,
                rich_heading(lang["generic_error_title"], level=3)
                + rich_note(f"<code>{rich_esc(e)}</code>"),
            )

        return

    # ── Queue completely finished (AutoPlay OFF or nothing usable found) ───────
    await leave_vc(chat_id)

    await rich_send(
        bot, chat_id,
        rich_heading(lang["queue_finished_title"], level=3)
        + rich_note(lang["queue_finished_note"]),
    )


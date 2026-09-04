# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

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
from ShizuMusic.utils.rich_ui import rich_esc, rich_heading, rich_kv_table, rich_note, rich_send


async def leave_vc(chat_id: int) -> None:
    """
    Leave voice chat and clean queue + autoplay state.
    """

    # Stop autoplay when leaving VC
    try:
        from ShizuMusic.core.autoplay import stop_autoplay
        stop_autoplay(chat_id)
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


@call_py.on_update(fl.stream_end())
async def on_stream_end(_: object, update: StreamEnded) -> None:
    """
    Automatically play the next song when the current stream ends.
    AutoPlay mode also refetches songs when queue becomes low.
    """

    chat_id = update.chat_id

    # Remove finished song
    done = pop_current(chat_id)

    if done:
        await asyncio.sleep(1)

        try:
            delete_file(done.get("file_path", ""))

        except Exception:
            pass

    # ── AutoPlay Refetch Check ────────────────────────────────────────────────
    try:
        from ShizuMusic.core.autoplay import is_autoplay, maybe_refetch

        if is_autoplay(chat_id):

            # Fetch more songs in background if queue is getting low
            asyncio.create_task(
                maybe_refetch(chat_id, "🔁 AutoPlay", 0)
            )

    except Exception as ap_err:
        LOGGER.warning(f"[AutoPlay] Refetch Check Error: {ap_err}")

    # ── Next Song ─────────────────────────────────────────────────────────────
    # Wait a little so autoplay fetch can complete
    await asyncio.sleep(2)

    nxt = peek_current(chat_id)

    # Play next song
    if nxt:

        from ShizuMusic.core.player import play_song

        try:
            msg = await rich_send(
                bot, chat_id,
                rich_heading("❍ ɴᴇxᴛ ᴛʀᴀᴄᴋ", level=3)
                + rich_kv_table([("ᴛɪᴛʟᴇ", f"<code>{rich_esc(nxt['title'])}</code>")]),
            )

            await play_song(chat_id, msg, nxt)

        except (NoActiveGroupCall, TelegramServerError) as e:
            LOGGER.error(f"Next Song VC Error: {e}")

        except Exception as e:
            LOGGER.error(f"Next Song Error: {e}")

            await rich_send(
                bot, chat_id,
                rich_heading("❍ ᴇʀʀᴏʀ", level=3)
                + rich_note(f"<code>{rich_esc(e)}</code>"),
            )

    else:

        # Queue finished but autoplay may still fetch songs
        try:
            from ShizuMusic.core.autoplay import (
                is_autoplay,
                _autoplay_fetching,
            )

            if is_autoplay(chat_id):

                # Wait if background fetching is running (up to 20 seconds)
                for _ in range(20):
                    if _autoplay_fetching.get(chat_id):
                        await asyncio.sleep(1)
                    else:
                        break

                # Give one more second after fetching finishes
                await asyncio.sleep(1)

                nxt2 = peek_current(chat_id)

                # Play fetched song
                if nxt2:

                    from ShizuMusic.core.player import play_song

                    msg2 = await rich_send(
                        bot, chat_id,
                        rich_heading("❍ ɴᴇxᴛ ᴛʀᴀᴄᴋ", level=3)
                        + rich_kv_table([("ᴛɪᴛʟᴇ", f"<code>{rich_esc(nxt2['title'])}</code>")]),
                    )

                    await play_song(chat_id, msg2, nxt2)
                    return

                # If still nothing after waiting, try one more fetch
                from ShizuMusic.core.autoplay import maybe_refetch
                await maybe_refetch(chat_id, "🔁 AutoPlay", 0)
                await asyncio.sleep(5)

                nxt3 = peek_current(chat_id)
                if nxt3:
                    from ShizuMusic.core.player import play_song
                    msg3 = await rich_send(
                        bot, chat_id,
                        rich_heading("❍ ɴᴇxᴛ ᴛʀᴀᴄᴋ", level=3)
                        + rich_kv_table([("ᴛɪᴛʟᴇ", f"<code>{rich_esc(nxt3['title'])}</code>")]),
                    )
                    await play_song(chat_id, msg3, nxt3)
                    return

        except Exception:
            pass

        # Queue completely finished
        await leave_vc(chat_id)

        await rich_send(
            bot, chat_id,
            rich_heading("❍ ǫᴜᴇᴜᴇ ғɪɴɪsʜᴇᴅ", level=3)
            + rich_note("ʟᴇғᴛ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ."),
        )
        

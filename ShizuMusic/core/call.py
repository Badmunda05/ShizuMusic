# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio

from pyrogram.enums import ParseMode
from pytgcalls import filters as fl
from pytgcalls.types import StreamEnded, Update

from ShizuMusic import LOGGER, bot, call_py
from ShizuMusic.core.queue import clear_queue, peek_current, pop_current, queue_size
from ShizuMusic.utils.helpers import delete_file


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
            msg = await bot.send_message(
                chat_id,
                f"<b>❍ ɴᴇxᴛ ᴛʀᴀᴄᴋ :</b>\n"
                f"<b>❍ ᴛɪᴛʟᴇ :</b> <code>{nxt['title']}</code>",
                parse_mode=ParseMode.HTML,
            )

            await play_song(chat_id, msg, nxt)

        except Exception as e:
            LOGGER.error(f"Next Song Error: {e}")

            await bot.send_message(
                chat_id,
                f"<b>❍ ᴇʀʀᴏʀ :</b> <code>{e}</code>",
                parse_mode=ParseMode.HTML,
            )

    else:

        # Queue finished but autoplay may still fetch songs
        try:
            from ShizuMusic.core.autoplay import (
                is_autoplay,
                _autoplay_fetching,
            )

            if is_autoplay(chat_id):

                # Wait if background fetching is running
                for _ in range(8):

                    if _autoplay_fetching.get(chat_id):
                        await asyncio.sleep(1)

                    else:
                        break

                nxt2 = peek_current(chat_id)

                # Play fetched song
                if nxt2:

                    from ShizuMusic.core.player import play_song

                    msg2 = await bot.send_message(
                        chat_id,
                        f"<b>❍ ɴᴇxᴛ ᴛʀᴀᴄᴋ :</b> "
                        f"<code>{nxt2['title']}</code>",
                        parse_mode=ParseMode.HTML,
                    )

                    await play_song(chat_id, msg2, nxt2)
                    return

        except Exception:
            pass

        # Queue completely finished
        await leave_vc(chat_id)

        await bot.send_message(
            chat_id,
            "<b>❍ ǫᴜᴇᴜᴇ ꜰɪɴɪꜱʜᴇᴅ</b>\n"
            "<b>❍ ʟᴇꜰᴛ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ.</b>",
            parse_mode=ParseMode.HTML,
        )

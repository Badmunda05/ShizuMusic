# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio
import time
import os

from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pytgcalls.types import AudioQuality, MediaStream

import config
from ShizuMusic import LOGGER, bot, call_py
from ShizuMusic.utils.formatters import fmt_time, parse_dur, progress_bar, short
from ShizuMusic.utils.youtube import resolve_stream


# ── Progress updater ──────────────────────────────────────────────────────────

async def _update_progress(
    chat_id: int,
    msg: Message,
    start_t: float,
    total: float,
    caption: str,
) -> None:
    btns = [
        InlineKeyboardButton("▷",   callback_data="resume"),
        InlineKeyboardButton("II",  callback_data="pause"),
        InlineKeyboardButton("‣‣I", callback_data="skip"),
        InlineKeyboardButton("▢",   callback_data="stop"),
    ]
    while True:
        elapsed = min(time.time() - start_t, total)
        bar = progress_bar(elapsed, total)
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(bar, callback_data="noop")],
            btns,
        ])
        try:
            await bot.edit_message_caption(chat_id, msg.id, caption=caption, reply_markup=kb)
        except Exception as e:
            if "MESSAGE_NOT_MODIFIED" not in str(e):
                break
        if elapsed >= total:
            break
        await asyncio.sleep(18)


# ── VC auto-start helper ──────────────────────────────────────────────────────

async def _ensure_vc(chat_id: int) -> None:
    """Create voice chat via assistant if not already active."""
    from ShizuMusic import assistant
    import random
    try:
        await assistant.invoke(
            __import__("pyrogram.raw.functions.phone", fromlist=["CreateGroupCall"])
            .CreateGroupCall(
                peer=await assistant.resolve_peer(chat_id),
                random_id=random.randint(10000, 99999),
            )
        )
        LOGGER.info(f"[VC] Created voice chat in {chat_id}")
        await asyncio.sleep(2)
    except Exception as e:
        err = str(e).lower()
        if "already" in err or "groupcall_already_started" in err:
            pass
        else:
            LOGGER.warning(f"[VC] Could not create VC: {e}")


# ── Main play function ────────────────────────────────────────────────────────

async def play_song(chat_id: int, message: Message, song: dict) -> None:
    url = song.get("url")
    if not url:
        return

    loading_text = f"<b>❍ ʟᴏᴀᴅɪɴɢ :</b> {short(song['title'])}"
    try:
        await message.edit(loading_text, parse_mode=ParseMode.HTML)
    except Exception:
        message = await bot.send_message(chat_id, loading_text, parse_mode=ParseMode.HTML)

    # Resolve audio
    try:
        media_path = await resolve_stream(url)
    except Exception as e:
        await bot.send_message(
            chat_id,
            f"<b>❍ ᴅᴏᴡɴʟᴏᴀᴅ ғᴀɪʟᴇᴅ</b>\n\n<code>{e}</code>\n\n"
            "<i>ᴩʟᴇᴀsᴇ ᴛʀʏ /play ᴀɢᴀɪɴ</i>",
            parse_mode=ParseMode.HTML,
        )
        return

    # Play — auto-create VC if needed
    for attempt in range(2):
        try:
            # ── Alpha Music Intro Logic ───────────────────────────────────────
            # Pehle ElevenLabs wala audio bajega agar file maujood hai
            intro_path = "alpha.mp3"
            if os.path.exists(intro_path):
                try:
                    await call_py.play(
                        chat_id,
                        MediaStream(
                            intro_path,
                            audio_parameters=AudioQuality.HIGH,
                            video_flags=MediaStream.Flags.IGNORE,
                        ),
                    )
                    # Intro bajne ke liye 3-4 second ka wait (audio length ke hisaab se)
                    await asyncio.sleep(4) 
                except Exception as e:
                    LOGGER.warning(f"[Alpha] Intro play failed: {e}")

            # Ab asli gaana play hoga
            await call_py.play(
                chat_id,
                MediaStream(
                    media_path,
                    audio_parameters=AudioQuality.HIGH,
                    video_flags=MediaStream.Flags.IGNORE,
                ),
            )
            break
        except Exception as e:
            if "group_call_not_found" in str(e).lower() and attempt == 0:
                await _ensure_vc(chat_id)
                continue
            else:
                await bot.send_message(chat_id, f"<b>❍ ᴇʀʀᴏʀ:</b> <code>{e}</code>")
                return

    # Caption and Progress
    dur_str = song.get("duration", "0:00")
    total_s = parse_dur(dur_str)
    
    caption = (
        "<b>╭──────────────────────▣</b>\n"
        "<b>│❍ ᴀʟᴘʜᴀ ʙᴏᴛs ᴏғғɪᴄɪᴀʟ🥀</b>\n"
        "<b>├──────────────────────▣</b>\n"
        f"<b>│❍ ᴛɪᴛʟᴇ :</b> {short(song['title'])}\n"
        f"<b>│❍ ᴅᴜʀᴀᴛɪᴏɴ :</b> {dur_str}\n"
        "<b>╰──────────────────────▣</b>"
    )

    # Edit original message with player UI
    await message.delete()
    player_msg = await bot.send_photo(
        chat_id,
        photo=song.get("thumbnail"),
        caption=caption,
        parse_mode=ParseMode.HTML,
    )
    
    # Start background progress task
    asyncio.create_task(_update_progress(chat_id, player_msg, time.time(), float(total_s), caption))
    

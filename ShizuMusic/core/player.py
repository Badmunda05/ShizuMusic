# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio
import time

from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pytgcalls.types import AudioQuality, MediaStream, VideoQuality

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

    is_video = song.get("video", False)

    # Play — auto-create VC if needed
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
            break
        except Exception as e:
            err = str(e).lower()
            vc_missing = any(k in err for k in (
                "groupcallnotfound", "not_in_group_call",
                "groupcall_forbidden", "not in group call",
                "no active group call",
            ))
            if vc_missing and attempt == 0:
                LOGGER.info(f"[VC] Not active in {chat_id} — creating…")
                await _ensure_vc(chat_id)
                continue
            await bot.send_message(
                chat_id,
                f"<b>❍ ᴘʟᴀʏʙᴀᴄᴋ ғᴀɪʟᴇᴅ :</b> <code>{e}</code>\n\n"
                "<i>ᴍᴀᴋᴇ ꜱᴜʀᴇ ᴀꜱꜱɪꜱᴛᴀɴᴛ ɪꜱ ɪɴ ᴛʜᴇ ɢʀᴏᴜᴘ ᴀɴᴅ ᴠᴄ ᴄᴀɴ ʙᴇ ꜱᴛᴀʀᴛᴇᴅ.</i>",
                parse_mode=ParseMode.HTML,
            )
            return

    # ── DB: track play count ──────────────────────────────────────────────────
    try:
        from ShizuMusic.database import add_served_chat, add_served_user, increment_play_count
        add_served_chat(chat_id)
        requester_id = song.get("requester_id")
        if requester_id:
            add_served_user(requester_id)
        increment_play_count(chat_id)
    except Exception as db_err:
        LOGGER.warning(f"[DB] play_song tracking failed: {db_err}")

    # Build now-playing UI
    total   = parse_dur(song.get("duration", "0:00"))
    caption = (
        "<blockquote>"
        "<b>🎧 Sʜɪᴢᴜ Mᴜsɪᴄ</b>\n\n"
        f"<b>❍ ᴛɪᴛʟᴇ :</b> {short(song['title'])}\n"
        f"<b>❍ ᴅᴜʀ   :</b> {song.get('duration', '?')}\n"
        f"<b>❍ ʙʏ    :</b> {song['requester']}"
        "</blockquote>"
    )
    btns = [
        InlineKeyboardButton("▷",   callback_data="resume"),
        InlineKeyboardButton("II",  callback_data="pause"),
        InlineKeyboardButton("‣‣I", callback_data="skip"),
        InlineKeyboardButton("▢",   callback_data="stop"),
    ]
    bar = progress_bar(0, total)
    kb  = InlineKeyboardMarkup([
        [InlineKeyboardButton(bar, callback_data="noop")],
        btns,
    ])

    thumb = song.get("thumbnail")
    try:
        pmsg = await message.reply_photo(
            photo=thumb, caption=caption, reply_markup=kb, parse_mode=ParseMode.HTML
        )
    except Exception:
        pmsg = await bot.send_message(chat_id, caption, reply_markup=kb, parse_mode=ParseMode.HTML)

    try:
        await message.delete()
    except Exception:
        pass

    asyncio.create_task(_update_progress(chat_id, pmsg, time.time(), total, caption))

    if config.LOGGER_ID:
        asyncio.create_task(bot.send_message(
            config.LOGGER_ID,
            "<b>#ɴᴏᴡᴘʟᴀʏɪɴɢ</b>\n"
            f"• <b>ᴛɪᴛʟᴇ :</b> {song.get('title')}\n"
            f"• <b>ᴅᴜʀ   :</b> {song.get('duration')}\n"
            f"• <b>ʙʏ    :</b> {song.get('requester')}",
            parse_mode=ParseMode.HTML,
        ))

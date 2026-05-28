# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
# --------------------------------------------------------------------------------

import asyncio
import random
import time

from pyrogram.enums import ParseMode
from pyrogram.raw.functions.phone import CreateGroupCall
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from pytgcalls.types import (
    AudioQuality,
    MediaStream,
    VideoQuality,
)

import config

from ShizuMusic import (
    LOGGER,
    assistant,
    bot,
    call_py,
)

from ShizuMusic.utils.formatters import (
    parse_dur,
    progress_bar,
    short,
)

from ShizuMusic.utils.youtube import resolve_stream


# ─────────────────────────────────────────────
# PROGRESS UPDATER
# ─────────────────────────────────────────────

async def _update_progress(
    chat_id: int,
    msg: Message,
    start_t: float,
    total: float,
    caption: str,
) -> None:

    buttons = [
        InlineKeyboardButton("▷", callback_data="resume"),
        InlineKeyboardButton("II", callback_data="pause"),
        InlineKeyboardButton("‣‣I", callback_data="skip"),
        InlineKeyboardButton("▢", callback_data="stop"),
    ]

    while True:

        elapsed = min(
            time.time() - start_t,
            total,
        )

        bar = progress_bar(
            elapsed,
            total,
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        bar,
                        callback_data="noop",
                    )
                ],
                buttons,
            ]
        )

        try:

            await bot.edit_message_caption(
                chat_id,
                msg.id,
                caption=caption,
                reply_markup=keyboard,
            )

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

    try:

        await assistant.invoke(
            CreateGroupCall(
                peer=await assistant.resolve_peer(chat_id),
                random_id=random.randint(
                    10000,
                    99999,
                ),
            )
        )

        LOGGER.info(
            f"[VC] Started in {chat_id}"
        )

        await asyncio.sleep(2)

        return True

    except Exception as e:

        err = str(e).lower()

        # VC already started
        if (
            "already" in err
            or "groupcall_already_started" in err
        ):
            return True

        # Admin permission missing
        if (
            "chat_admin_required" in err
            or "admin" in err
        ):

            await bot.send_message(
                chat_id,
                "<b>❍ ᴠᴄ ꜱᴛᴀʀᴛ ᴘᴇʀᴍɪssɪᴏɴ ᴍɪssɪɴɢ</b>\n\n"
                "<b>❍ ɢɪᴠᴇ ᴀssɪsᴛᴀɴᴛ :</b>\n"
                "• <code>Manage Video Chats</code>\n"
                "• <code>Admin Rights</code>",
                parse_mode=ParseMode.HTML,
            )

            return False

        LOGGER.warning(f"[VC ERROR] {e}")

        return False


# ─────────────────────────────────────────────
# MAIN PLAY FUNCTION
# ─────────────────────────────────────────────

async def play_song(
    chat_id: int,
    message: Message,
    song: dict,
) -> bool:

    url = song.get("url")

    if not url:
        return False

    loading = (
        f"<b>❍ ʟᴏᴀᴅɪɴɢ :</b> "
        f"{short(song['title'])}"
    )

    try:

        await message.edit(
            loading,
            parse_mode=ParseMode.HTML,
        )

    except Exception:

        message = await bot.send_message(
            chat_id,
            loading,
            parse_mode=ParseMode.HTML,
        )

    # ─────────────────────────────────────────
    # RESOLVE STREAM
    # ─────────────────────────────────────────

    try:

        media_path = await resolve_stream(url)

    except Exception as e:

        await bot.send_message(
            chat_id,
            f"<b>❍ ᴅᴏᴡɴʟᴏᴀᴅ ғᴀɪʟᴇᴅ</b>\n\n"
            f"<code>{e}</code>",
            parse_mode=ParseMode.HTML,
        )

        return False

    is_video = song.get("video", False)

    # ─────────────────────────────────────────
    # EFFECTS
    # ─────────────────────────────────────────

    if not is_video:

        try:

            from ShizuMusic.modules.effects import (
                maybe_apply_effects,
            )

            media_path = await maybe_apply_effects(
                chat_id,
                media_path,
            )

        except Exception as fx_err:

            LOGGER.warning(
                f"[Effects] {fx_err}"
            )

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

            # BUG FIX 1
            # Auto create VC then retry play
            if vc_missing and attempt == 0:

                LOGGER.info(
                    f"[VC] Creating VC in {chat_id}"
                )

                ok = await _ensure_vc(chat_id)

                if ok:
                    await asyncio.sleep(2)
                    continue

                return False

            # BUG FIX 2
            # Clean admin error text
            if (
                "chat_admin_required" in err
                or "admin" in err
            ):

                await bot.send_message(
                    chat_id,
                    "<b>❍ ᴀssɪsᴛᴀɴᴛ ɴᴜ ᴀᴅᴍɪɴ ʙɴᴀᴏ</b>\n\n"
                    "• <code>Manage Video Chats</code>\n"
                    "• <code>Delete Messages</code>",
                    parse_mode=ParseMode.HTML,
                )

                return False

            LOGGER.error(f"[PLAY ERROR] {e}")

            await bot.send_message(
                chat_id,
                "<b>❍ ᴘʟᴀʏʙᴀᴄᴋ ғᴀɪʟᴇᴅ</b>",
                parse_mode=ParseMode.HTML,
            )

            return False

    if not played:
        return False

    # ─────────────────────────────────────────
    # RESET SEEK
    # ─────────────────────────────────────────

    try:

        from ShizuMusic.modules.seek import (
            set_seek_state,
        )

        set_seek_state(chat_id, 0)

    except Exception:
        pass

    # ─────────────────────────────────────────
    # DB TRACKING
    # ─────────────────────────────────────────

    try:

        from ShizuMusic.database import (
            add_served_chat,
            add_served_user,
            increment_play_count,
        )

        add_served_chat(chat_id)

        requester_id = song.get(
            "requester_id"
        )

        if requester_id:
            add_served_user(requester_id)

        increment_play_count(chat_id)

    except Exception as db_err:

        LOGGER.warning(
            f"[DB] {db_err}"
        )

    # ─────────────────────────────────────────
    # NOW PLAYING UI
    # ─────────────────────────────────────────

    total = parse_dur(
        song.get("duration", "0:00")
    )

    caption = (
        "<blockquote>"
        "<b>🎧 Sʜɪᴢᴜ Mᴜsɪᴄ</b>\n\n"
        f"<b>❍ ᴛɪᴛʟᴇ :</b> "
        f"{short(song['title'])}\n"
        f"<b>❍ ᴅᴜʀ :</b> "
        f"{song.get('duration', '?')}\n"
        f"<b>❍ ʙʏ :</b> "
        f"{song['requester']}"
        "</blockquote>"
    )

    buttons = [
        InlineKeyboardButton("▷", callback_data="resume"),
        InlineKeyboardButton("II", callback_data="pause"),
        InlineKeyboardButton("‣‣I", callback_data="skip"),
        InlineKeyboardButton("▢", callback_data="stop"),
    ]

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    progress_bar(0, total),
                    callback_data="noop",
                )
            ],
            buttons,
        ]
    )

    thumb = song.get("thumbnail")

    try:

        pmsg = await message.reply_photo(
            photo=thumb,
            caption=caption,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )

    except Exception:

        pmsg = await bot.send_message(
            chat_id,
            caption,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )

    try:
        await message.delete()
    except Exception:
        pass

    asyncio.create_task(
        _update_progress(
            chat_id,
            pmsg,
            time.time(),
            total,
            caption,
        )
    )

    # ─────────────────────────────────────────
    # LOGGER
    # ─────────────────────────────────────────

    if config.LOGGER_ID:

        asyncio.create_task(
            bot.send_message(
                config.LOGGER_ID,
                "<b>#ɴᴏᴡᴘʟᴀʏɪɴɢ</b>\n"
                f"• <b>ᴛɪᴛʟᴇ :</b> {song.get('title')}\n"
                f"• <b>ᴅᴜʀ :</b> {song.get('duration')}\n"
                f"• <b>ʙʏ :</b> {song.get('requester')}",
                parse_mode=ParseMode.HTML,
            )
        )

    return True

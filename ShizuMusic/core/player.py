# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
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

from ShizuMusic.utils.formatters import (
    parse_dur,
    progress_bar,
    short,
)

from ShizuMusic.utils.rich_ui import (
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
)

def _support_updates_pills() -> str:
    return (
        "<p>"
        f'<tg-button type="url" style="primary" url="{config.SUPPORT_GROUP}">'
        "🍬 sᴜᴘᴘᴏʀᴛ</tg-button> "
        f'<tg-button type="url" style="success" url="{config.UPDATES_CHANNEL}">'
        "🍹 ᴜᴘᴅᴀᴛᴇs</tg-button>"
        "</p>"
    )


# ─────────────────────────────────────────────
# NOW PLAYING CONTENT
# ─────────────────────────────────────────────


def _now_playing_content(song: dict) -> str:
    """Now-playing rich message content."""

    thumb = song.get("thumbnail")

    return (
        rich_heading(
            "🎧 sʜɪᴢᴜ ᴍᴜsɪᴄ — ɴᴏᴡ ᴘʟᴀʏɪɴɢ",
            level=3
        )
        + (rich_img(thumb) if thumb else "")
        + rich_kv_table([
            ("ᴛɪᴛʟᴇ", rich_esc(short(song["title"]))),
            ("ᴅᴜʀᴀᴛɪᴏɴ", rich_esc(song.get("duration", "?"))),
            ("ʙʏ", rich_esc(song["requester"])),
        ])
        + _support_updates_pills()
    )


def _now_playing_kb(elapsed: float, total: float) -> InlineKeyboardMarkup:
    bar = progress_bar(elapsed, total)
    btns = [
        InlineKeyboardButton("▷", callback_data="resume"),
        InlineKeyboardButton("II", callback_data="pause"),
        InlineKeyboardButton("‣‣I", callback_data="skip"),
        InlineKeyboardButton("▢", callback_data="stop"),
    ]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(bar, callback_data="noop")],
        btns,
    ])


# ─────────────────────────────────────────────
# PROGRESS UPDATER
# ─────────────────────────────────────────────

async def _update_progress(
    chat_id: int,
    msg: Message,
    start_t: float,
    total: float,
    content: str,
) -> None:

    while True:

        elapsed = min(time.time() - start_t, total)
        kb = _now_playing_kb(elapsed, total)

        try:
            await rich_edit(msg, content, reply_markup=kb)

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
            rich_heading("❍ ᴠᴄ sᴛᴀʀᴛ ғᴀɪʟᴇᴅ (Telegram Server)", level=3)
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
                rich_heading("❍ ᴠᴄ sᴛᴀʀᴛ ᴘᴇʀᴍɪssɪᴏɴ ᴍɪssɪɴɢ", level=3)
                + rich_note("ɢɪᴠᴇ ᴀssɪsᴛᴀɴᴛ » ᴍᴀɴᴀɢᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛs, ᴀᴅᴍɪɴ ʀɪɢʜᴛs"),
            )
            return False

        LOGGER.error(f"[VC ERROR] {e}")
        await rich_send(
            bot, chat_id,
            rich_heading("❍ ᴠᴄ sᴛᴀʀᴛ ғᴀɪʟᴇᴅ", level=3)
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
    url = song.get("url")

    if not url:
        return

    loading_text = (
        rich_heading("❍ ʟᴏᴀᴅɪɴɢ...", level=3)
        + rich_kv_table([("sᴏɴɢ", rich_esc(short(song['title'])))])
    )

    try:
        await rich_edit(message, loading_text)

    except Exception:
        message = await rich_send(bot, chat_id, loading_text)

    # ─────────────────────────────────────────
    # RESOLVE STREAM
    # ─────────────────────────────────────────

    try:
        media_path = await resolve_stream(url)

    except Exception as e:
        try:
            remove_from_queue(chat_id, 0)
        except Exception:
            pass

        await rich_send(
            bot, chat_id,
            rich_heading("❍ ᴅᴏᴡɴʟᴏᴀᴅ ғᴀɪʟᴇᴅ", level=3)
            + rich_note(f"<code>{rich_esc(e)}</code>"),
        )
        return

    is_video = song.get("video", False)

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
                rich_heading("❍ ᴘʟᴀʏʙᴀᴄᴋ ғᴀɪʟᴇᴅ (Telegram Server)", level=3)
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
                    rich_heading("❍ ᴠᴄ sᴛᴀʀᴛ ᴘᴇʀᴍɪssɪᴏɴ ᴍɪssɪɴɢ", level=3)
                    + rich_note("ᴘʟᴇᴀsᴇ ɢɪᴠᴇ » ᴍᴀɴᴀɢᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛs, ᴀᴅᴍɪɴ ʀɪɢʜᴛs · "
                                "ᴀssɪsᴛᴀɴᴛ ᴍᴜsᴛ ʙᴇ ᴀᴅᴍɪɴ"),
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
                rich_heading("❍ ᴘʟᴀʏʙᴀᴄᴋ ғᴀɪʟᴇᴅ", level=3)
                + rich_note(f"<code>{rich_esc(e)}</code>"),
            )
            LOGGER.error(f"[PLAY ERROR] {e}")
            return

    if not played:
        return

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

        add_served_chat(chat_id)
        requester_id = song.get("requester_id")

        if requester_id:
            add_served_user(requester_id)

        increment_play_count(chat_id)

    except Exception as db_err:
        LOGGER.warning(f"[DB ERROR] {db_err}")

    # ─────────────────────────────────────────
    # NOW PLAYING UI — one genuine rich message (heading + embedded
    # thumbnail + table). This message is edited every ~18s for the
    # progress bar, so it has to stay a true rich text message rather
    # than a photo caption (captions can never carry rich blocks).
    # ─────────────────────────────────────────

    total = parse_dur(song.get("duration", "0:00"))
    content = _now_playing_content(song)
    kb = _now_playing_kb(0, total)

    try:
        pmsg = await rich_edit(message, content, reply_markup=kb)
        if pmsg is None:
            pmsg = message
    except Exception:
        pmsg = await rich_send(bot, chat_id, content, reply_markup=kb)

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

    if config.LOGGER_ID:
        asyncio.create_task(
            bot.send_message(
                config.LOGGER_ID,
                "<b>#ɴᴏᴡᴘʟᴀʏɪɴɢ</b>\n"
                f"• <b>ᴛɪᴛʟᴇ :</b> {rich_esc(song.get('title'))}\n"
                f"• <b>ᴅᴜʀ :</b> {rich_esc(song.get('duration'))}\n"
                f"• <b>ʙʏ :</b> {rich_esc(song.get('requester'))}",
                parse_mode=ParseMode.HTML,
            )
        )

                                      

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

from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery

import config
from ShizuMusic import bot, call_py
from ShizuMusic.core.call import leave_vc
from ShizuMusic.core.player import play_song
from ShizuMusic.core.queue import clear_queue, peek_current, pop_current, queue_size
from ShizuMusic.utils.buttons import (
    help_back_kb,
    help_menu_home_kb,
    player_controls_kb,
    start_private_kb,
    support_updates_pills,
)
from ShizuMusic.utils.db import is_thumbnail_enabled, is_user_blocked_db, set_thumbnail_enabled
from ShizuMusic.utils.formatters import short
from ShizuMusic.utils.helpers import delete_file
from ShizuMusic.utils.language import chat_strings
from ShizuMusic.utils.routes import panel_target
from ShizuMusic.utils.permissions import is_user_authorized
from richgram import (
    rich_details,
    rich_esc,
    rich_heading,
    rich_img,
    rich_kv_table,
    rich_note,
    rich_send,
    rich_table,
    rich_edit,
    sanitize_display_name,
)

def _category_html(lang: dict, title: str, desc: str, rows, photo: str = None) -> str:
    """title/desc/rows + photo -> photo + heading + description + Command/Description table + pills."""
    html = ""
    if photo:
        html += rich_img(photo)
    return (
        html
        + rich_heading(title, level=3)
        + f"<p>{desc}</p>"
        + rich_table([lang["kv_command"], lang["kv_description"]], rows)
        + support_updates_pills(lang)
    )


# ── Help menu layout ──────────────────────────────────────────────────────────
#
#   Row 1 : [ᴧᴅᴍɪɴ]  [ᴧ-ᴘʟᴀʏ]  [ɢ-ᴄᴧsᴛ]
#   Row 2 : [ʙʟ-ᴄʜᴧᴛ] [ʙʟ-ᴜsᴇʀs] [ᴘɪɴɢ]
#   Row 3 : [ᴘʟᴀʏ]   [sᴘᴇᴇᴅ]   [ɪɴғᴏ]
#   Row 4 :          [⌯ ʜᴏᴍᴇ ⌯]
#
# ──────────────────────────────────────────────────────────────────

# Help keyboards are built per-request now (with the chat's language) —


def _onboarding_body(lang: dict, uid: int, name: str) -> str:
    """Same private-chat onboarding text as modules/start.py — used by 'go back'."""
    return (
        rich_note(
            lang["onboarding_greeting"].format(uid, rich_esc(name))
            + lang["onboarding_intro"].format(rich_esc(config.BOT_NAME))
        )
        + rich_details(
            lang["onboarding_features_heading"],
            rich_table(lang["onboarding_features_headers"], lang["onboarding_features_rows"]),
            open=True,
        )
        + rich_details(
            lang["onboarding_why_heading"],
            lang["onboarding_why_body"],
            open=True,
        )
        + rich_note(lang["onboarding_powered_by"])
        + support_updates_pills(lang)
    )


async def _refresh_player_kb(cbq: CallbackQuery, chat_id: int, lang: dict) -> None:
    """Redraw the player buttons in place (after a toggle) — keeps the progress bar.

    The buttons are part of the rich message now, so the whole message is
    re-edited: same card content + fresh buttons.
    """
    try:
        from ShizuMusic.core.player import _now_playing_content, get_panel_content
        from ShizuMusic.modules.seek import get_current_position
        from ShizuMusic.utils.formatters import parse_dur

        song    = peek_current(chat_id)
        total   = parse_dur(song.get("duration", "0:00")) if song else 0
        elapsed = min(get_current_position(chat_id), total) if song else 0

        content = get_panel_content(chat_id, cbq.message.id)
        if content is None and song:
            content = _now_playing_content(song, lang, is_thumbnail_enabled(chat_id))
        if content is None:
            return

        await rich_edit(
            cbq.message,
            content + player_controls_kb(elapsed, total, chat_id, lang),
        )
    except Exception:
        pass   # "message not modified" / message already gone


# ══════════════════════════════════════════════════════════════════
#  MAIN CALLBACK HANDLER
# ══════════════════════════════════════════════════════════════════

@bot.on_callback_query()
async def on_callback(client, cbq: CallbackQuery) -> None:

    # a player panel of a linked channel sits in the group but controls the channel VC
    chat_id = panel_target(cbq.message.chat.id, cbq.message.id)
    user    = cbq.from_user
    data    = cbq.data
    lang    = chat_strings(chat_id)

    # ── Block check ──────────────────────────────────────────────────────────
    if user and is_user_blocked_db(user.id):
        await cbq.answer()
        return

    # ── Admin check for playback controls ─────────────────────────────────────
    if data in ("pause", "resume", "skip", "stop", "clear", "thumb_toggle", "autoplay_toggle"):
        if not await is_user_authorized(cbq):
            await cbq.answer(lang["cb_admins_only"], show_alert=True)
            return

    # ── PAUSE ────────────────────────────────────────────────────────────
    if data == "pause":
        try:
            await call_py.pause(chat_id)
            await cbq.answer(lang["cb_paused_toast"])
            await rich_send(
                bot, chat_id,
                rich_heading(lang["pause_title"], level=3)
                + rich_note(lang["cb_by_footer"].format(user.mention)),
            )
        except Exception:
            await cbq.answer(lang["cb_pause_failed_toast"], show_alert=True)

    # ── RESUME ────────────────────────────────────────────────────────────
    elif data == "resume":
        try:
            await call_py.resume(chat_id)
            await cbq.answer(lang["cb_resumed_toast"])
            await rich_send(
                bot, chat_id,
                rich_heading(lang["resume_title"], level=3)
                + rich_note(lang["cb_by_footer"].format(user.mention)),
            )
        except Exception:
            await cbq.answer(lang["cb_resume_failed_toast"], show_alert=True)

    # ── SKIP ────────────────────────────────────────────────────────────
    elif data == "skip":
        if not queue_size(chat_id):
            await cbq.answer(lang["cb_queue_empty_toast"], show_alert=True)
            return

        skipped = pop_current(chat_id)

        try:
            delete_file(skipped.get("file_path", ""))
        except Exception:
            pass

        await rich_send(
            bot, chat_id,
            rich_heading(lang["skip_skipped_title"], level=3)
            + rich_kv_table([
                (lang["kv_by"], user.mention),
                (lang["kv_song"], f"<code>{rich_esc(short(skipped['title']))}</code>"),
            ]),
        )

        nxt = peek_current(chat_id)

        if not nxt:
            # queue is empty: let AutoPlay (if ON) add one related song
            try:
                from ShizuMusic.core.autoplay import autoplay_next
                if await autoplay_next(chat_id, skipped):
                    nxt = peek_current(chat_id)
            except Exception:
                pass

        if nxt:
            try:
                from ShizuMusic.core.autoplay import schedule_prefetch
                schedule_prefetch(chat_id, nxt)
            except Exception:
                pass

            await cbq.answer(lang["cb_playing_next_toast"])
            dm = await rich_send(
                bot, chat_id,
                rich_heading(lang["next_track_title"], level=3)
                + rich_kv_table([
                    (lang["kv_song"], f"<code>{rich_esc(short(nxt['title']))}</code>"),
                ]),
            )
            await play_song(chat_id, dm, nxt)
        else:
            await cbq.answer(lang["cb_queue_empty_toast"], show_alert=True)

    # ── STOP ────────────────────────────────────────────────────────────
    elif data == "stop":
        await leave_vc(chat_id)
        await cbq.answer(lang["cb_stopped_toast"])
        await rich_send(
            bot, chat_id,
            rich_heading(lang["stop_stopped_title"], level=3)
            + rich_note(lang["cb_by_footer"].format(user.mention)),
        )

    # ── CLEAR ────────────────────────────────────────────────────────────
    elif data == "clear":
        clear_queue(chat_id)
        await cbq.answer(lang["cb_queue_cleared_toast"])
        await rich_edit(
            cbq.message,
            rich_heading(lang["clear_cleared_title"], level=3)
            + rich_note(lang["cb_by_footer"].format(user.mention)),
        )

    # ── THUMBNAIL ON/OFF (button on the player) ───────────────────────────
    elif data == "thumb_toggle":
        new_state = not is_thumbnail_enabled(chat_id)
        set_thumbnail_enabled(chat_id, new_state)
        await cbq.answer(lang["thumb_enabled_toast"] if new_state else lang["thumb_disabled_toast"])
        # button flips now; the card itself changes from the next song
        await _refresh_player_kb(cbq, chat_id, lang)

    # ── AUTOPLAY ON/OFF (button on the player) ────────────────────────────
    elif data == "autoplay_toggle":
        from ShizuMusic.core.autoplay import toggle_autoplay

        enabled = toggle_autoplay(chat_id)
        await cbq.answer(lang["autoplay_toggle_on_toast"] if enabled else lang["autoplay_toggle_off_toast"])
        await _refresh_player_kb(cbq, chat_id, lang)

    # ── CLOSE PLAYER PANEL (song keeps playing) ───────────────────────────
    elif data == "close_player":
        await cbq.answer()
        try:
            from ShizuMusic.core.player import mark_panel_closed
            mark_panel_closed(chat_id, cbq.message.id)
        except Exception:
            pass
        try:
            await cbq.message.delete()
        except Exception:
            pass
        try:
            note = await rich_send(
                bot, chat_id,
                rich_note(lang["player_closed_by"].format(user.mention)),
            )
            await asyncio.sleep(2)
            await note.delete()
        except Exception:
            pass

    # ── NOOP ────────────────────────────────────────────────────────────
    elif data == "noop":
        await cbq.answer()

    # ── CLOSE HELP ──────────────────────────────────────────────────────────
    elif data == "close_help":
        await cbq.answer()
        try:
            await cbq.message.delete()
        except Exception:
            pass

    # ── HELP ────────────────────────────────────────────────────────────
    elif data == "show_help":
        await cbq.answer()
        uid  = cbq.from_user.id
        name = sanitize_display_name(cbq.from_user.first_name)
        photo = random.choice(config.START_PHOTOS)
        content = (
            rich_heading(lang["help_pick_category_title"], level=3)
            + rich_img(photo)
            + rich_note(lang["help_pick_category_note"].format(uid, rich_esc(name)))
            + rich_details(
                    lang["help_features_heading"],
                    rich_table(lang["onboarding_features_headers"], lang["help_features_rows"]),
                    open=True,
                )
            + rich_note(lang["onboarding_powered_by"])
            + support_updates_pills(lang)
        )
        kb = help_menu_home_kb(lang)
        if getattr(cbq.message, "photo", None):
            # /start's message is a photo — can't edit its caption into a
            # true rich message, so swap it out for one.
            try:
                await cbq.message.delete()
            except Exception:
                pass
            await rich_send(bot, chat_id, content + kb)
        else:
            await rich_edit(cbq.message, content + kb)

    elif data == "go_back":
        await _go_back(cbq, lang)

    elif data.startswith("help_"):
        await cbq.answer()
        photo = random.choice(config.START_PHOTOS)
        help_data = lang["help_categories"].get(data)
        if help_data:
            rows = list(help_data["rows"])
            if data == "help_play":
                # dynamic, config-driven — can't be baked into the static yml text
                rows = rows + [
                    (lang["help_play_max_duration"],
                     lang["help_play_max_duration_val"].format(config.MAX_DURATION_SECONDS // 60)),
                    (lang["help_play_queue_limit"],
                     lang["help_play_queue_limit_val"].format(config.QUEUE_LIMIT)),
                    tuple(lang["help_thumbnail_row"]),
                ]
            text = _category_html(lang, help_data["title"], help_data["desc"], rows, photo)
            await rich_edit(cbq.message, text + help_back_kb(lang))


# ── Go back to start message ───────────────────────────────────────────────────

async def _go_back(cbq: CallbackQuery, lang: dict) -> None:
    await cbq.answer()
    uid  = cbq.from_user.id
    name = sanitize_display_name(cbq.from_user.first_name)
    photo = random.choice(config.START_PHOTOS)

    caption = rich_img(photo) + _onboarding_body(lang, uid, name)
    kb = start_private_kb(lang)

    chat_id = cbq.message.chat.id

    try:
        await cbq.message.delete()
    except Exception:
        pass

    await rich_send(bot, chat_id, caption + kb)
    

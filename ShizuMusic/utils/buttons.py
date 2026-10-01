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

import random
from typing import Optional

from pyrogram import enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import config
from ShizuMusic.utils.db import is_thumbnail_enabled
from ShizuMusic.utils.formatters import progress_bar
from richgram import rich_esc


def _t(lang: Optional[dict], key: str, default: str) -> str:
    return (lang or {}).get(key, default)


def _tg_btn(text: str, callback_data: str, style: Optional[str] = None) -> str:
    style_attr = f' style="{style}"' if style else ""
    return (
        f'<tg-button type="callback_data"{style_attr} '
        f'data="{callback_data}">{text}</tg-button>'
    )


def _url_btn(text: str, url: str, style: Optional[str] = None) -> str:
    """Rich-message URL button — identical layout to the Support/Updates pills."""
    style_attr = f' style="{style}"' if style else ""
    return f'<tg-button type="url"{style_attr} url="{url}">{text}</tg-button>'


def _lbl(lang: Optional[dict], key: str, default: str) -> str:
    """Localized label, HTML-escaped (labels contain '&')."""
    return rich_esc(_t(lang, key, default))


def random_style() -> str:
    """Random button colour — changes on every redraw (the panel refreshes every ~18s)."""
    return random.choice(["success", "danger", "primary"])


def _bar_style(elapsed: float, total: float) -> str:
    """Progress-bar colour follows the progress, same bands as the inline-keyboard player."""
    pct = int((elapsed / total) * 100) if total else 0
    if pct <= 10:
        return "primary"
    if pct < 20:
        return "success"
    if pct < 30:
        return "danger"
    if pct < 40:
        return "primary"
    if pct < 50:
        return "success"
    if pct < 60:
        return "danger"
    if pct < 70:
        return "primary"
    if pct < 80:
        return "success"
    if pct < 95:
        return "danger"
    return "primary"


def _row(*buttons: str) -> str:
    """One full-width row of buttons (buttons share the row equally, like Pixal Music)."""
    return "<tg-button-row>" + "".join(buttons) + "</tg-button-row>"


# ═════════════════════════════════════════════════════════════════════════════
# PLAYER CONTROLS  (now-playing message + /seek result)
# ═════════════════════════════════════════════════════════════════════════════
def player_controls_kb(
    elapsed: float,
    total: float,
    chat_id: Optional[int] = None,
    lang: Optional[dict] = None,
) -> str:
    bar = progress_bar(elapsed, total)
    html = (
        _row(_tg_btn(rich_esc(bar), "noop", _bar_style(elapsed, total)))
        + _row(
            _tg_btn("ʀᴇsᴜᴍᴇ", "resume", random_style()),
            _tg_btn("ᴘᴀᴜsᴇ", "pause", random_style()),
            _tg_btn("sᴋɪᴘ", "skip", random_style()),
            _tg_btn("ᴇɴᴅ", "stop", random_style()),
        )
    )

    if chat_id is None:
        return html

    thumb_on = is_thumbnail_enabled(chat_id)
    try:
        from ShizuMusic.core.autoplay import is_autoplay  # lazy: avoids import cycles
        autoplay_on = is_autoplay(chat_id)
    except Exception:
        autoplay_on = False

    autoplay_label = (
        _t(lang, "btn_autoplay_on", "🍷 ᴀᴜᴛᴏᴘʟᴀʏ | ᴏɴ") if autoplay_on
        else _t(lang, "btn_autoplay_off", "🍷 ᴀᴜᴛᴏᴘʟᴀʏ | ᴏғғ")
    )
    thumb_label = (
        _t(lang, "btn_thumb_on", "🖼 ᴛʜᴜᴍʙ | ᴏɴ") if thumb_on
        else _t(lang, "btn_thumb_off", "🖼 ᴛʜᴜᴍʙ | ᴏғғ")
    )
    close_label = _t(lang, "btn_close", "⌯ ᴄʟᴏsᴇ ⌯")

    html += (
        _row(
            _tg_btn(autoplay_label, "autoplay_toggle", random_style()),
            _tg_btn(thumb_label, "thumb_toggle", random_style()),
        )
        # Close only hides this panel — the song keeps playing.
        + _row(_tg_btn(close_label, "close_player", "danger"))
    )
    return html


def support_updates_pills(lang: Optional[dict] = None) -> str:
    """Inline 'Support' / 'Updates' pill buttons for rich messages (localized)."""
    return (
        "<p>"
        f'<tg-button type="url" style="primary" url="{config.SUPPORT_GROUP}">'
        f'{_t(lang, "pill_support", "🍬 sᴜᴘᴘᴏʀᴛ")}</tg-button> '
        f'<tg-button type="url" style="success" url="{config.UPDATES_CHANNEL}">'
        f'{_t(lang, "pill_updates", "🍹 ᴜᴘᴅᴀᴛᴇs")}</tg-button>'
        "</p>"
    )


# ═════════════════════════════════════════════════════════════════════════════
# QUEUE
# ═════════════════════════════════════════════════════════════════════════════
def skip_clear_kb(lang: Optional[dict] = None) -> str:
    """Shown under 'Added to queue' when a song lands behind another one."""
    return _row(
        _tg_btn(_lbl(lang, "btn_skip", "⌯ sᴋɪᴘ ⌯"), "skip", random_style()),
        _tg_btn(_lbl(lang, "btn_clear", "⌯ ᴄʟᴇᴀʀ ⌯"), "clear", random_style()),
    )


# ═════════════════════════════════════════════════════════════════════════════
# SUPPORT / REPO
# ═════════════════════════════════════════════════════════════════════════════
def support_kb(lang: Optional[dict] = None) -> str:
    """Single 'Support' button (used by /ping)."""
    return _row(
        _url_btn(_lbl(lang, "btn_support", "🍬 sᴜᴘᴘᴏʀᴛ 🍬"), config.SUPPORT_GROUP, random_style()),
    )


def repo_kb(source_url: str, lang: Optional[dict] = None) -> str:
    """Source / Fork / Support / Updates grid (used by /repo)."""
    return (
        _row(
            _url_btn(_lbl(lang, "btn_source", "🍡 sᴏᴜʀᴄᴇ ᴄᴏᴅᴇ 🍡"), source_url, random_style()),
            _url_btn(_lbl(lang, "btn_fork", "🔱 ғᴏʀᴋ 🔱"), source_url, random_style()),
        )
        + _row(
            _url_btn(_lbl(lang, "btn_support", "🍬 sᴜᴘᴘᴏʀᴛ 🍬"), config.SUPPORT_GROUP, random_style()),
            _url_btn(_lbl(lang, "btn_updates", "🍹 ᴜᴘᴅᴀᴛᴇs 🍹"), config.UPDATES_CHANNEL, random_style()),
        )
    )


# ═════════════════════════════════════════════════════════════════════════════
# ADMIN INVITE  (new group / manual admin-request retry)
# ═════════════════════════════════════════════════════════════════════════════
def make_admin_kb(bot_id: int, styled: bool = False, lang: Optional[dict] = None) -> str:
    """'⚡ Make me admin ⚡' — deep-links straight to the bot's profile."""
    return _row(
        _url_btn(_lbl(lang, "btn_make_admin", "⚡ ᴍᴀᴋᴇ ᴍᴇ ᴀᴅᴍɪɴ ⚡"), f"tg://user?id={bot_id}", "danger"),
    )


def added_by_kb(user_id: int, user_name: str) -> InlineKeyboardMarkup:
    """Small '👤 <name>' button used on the new-group log card."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f"👤 {user_name}", user_id=user_id),
    ]])


# ═════════════════════════════════════════════════════════════════════════════
# /start
# ═════════════════════════════════════════════════════════════════════════════
def start_private_kb(lang: Optional[dict] = None) -> str:
    """Full 4-row panel shown on /start in a private chat."""
    return (
        _row(_url_btn(_lbl(lang, "btn_add_me", "⛩️ ᴧᴅᴅ мᴇ ʙᴧʙʏ ⛩️"), f"{config.BOT_LINK}?startgroup=true", random_style()))
        + _row(
            _url_btn(_lbl(lang, "btn_support", "🍬 sᴜᴘᴘᴏʀᴛ 🍬"), config.SUPPORT_GROUP, random_style()),
            _url_btn(_lbl(lang, "btn_updates", "🍹 ᴜᴘᴅᴀᴛᴇs 🍹"), config.UPDATES_CHANNEL, random_style()),
        )
        + _row(_tg_btn(_lbl(lang, "btn_help", "🏩 ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs 🏩"), "show_help", random_style()))
        + _row(
            _url_btn(_lbl(lang, "btn_owner", "🫧 ᴏᴡɴᴇʀ 🫧"), f"tg://user?id={config.OWNER_ID}", random_style()),
            _url_btn(_lbl(lang, "btn_source_short", "🍡 sᴏᴜʀᴄᴇ 🍡"), "https://github.com/Badmunda05/ShizuMusic/fork", random_style()),
        )
        + _row(_tg_btn(_lbl(lang, "btn_language", "🌐 ʟᴀɴɢᴜᴀɢᴇ"), "show_lang", random_style()))
    )


def start_group_kb(lang: Optional[dict] = None) -> str:
    """Short 2-row panel shown on /start inside a group."""
    return (
        _row(
            _url_btn(_lbl(lang, "btn_add_me", "⛩️ ᴧᴅᴅ мᴇ ʙᴧʙʏ ⛩️"), f"{config.BOT_LINK}?startgroup=true", random_style()),
            _url_btn(_lbl(lang, "btn_support", "🍬 sᴜᴘᴘᴏʀᴛ 🍬"), config.SUPPORT_GROUP, random_style()),
        )
        + _row(_tg_btn(_lbl(lang, "btn_help", "🏩 ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs 🏩"), "show_help", random_style()))
    )


# ═════════════════════════════════════════════════════════════════════════════
# HELP MENU
# ═════════════════════════════════════════════════════════════════════════════
def _help_grid(lang: Optional[dict] = None) -> str:
    """The 3x3 category grid shared by every /help keyboard (localized labels)."""

    def b(key: str, default: str, data: str) -> str:
        return _tg_btn(_lbl(lang, key, default), data, random_style())

    return (
        _row(
            b("help_btn_admin", "ᴧᴅᴍɪɴ", "help_admin"),
            b("help_btn_autoplay", "ᴧ-ᴘʟᴀʏ", "help_autoplay"),
            b("help_btn_gcast", "ɢ-ᴄᴧsᴛ", "help_gcast"),
        )
        + _row(
            b("help_btn_blchat", "ʙʟ-ᴄʜᴧᴛ", "help_blchat"),
            b("help_btn_blusers", "ʙʟ-ᴜsᴇʀs", "help_blusers"),
            b("help_btn_ping", "ᴘɪɴɢ", "help_ping"),
        )
        + _row(
            b("help_btn_play", "ᴘʟᴀʏ", "help_play"),
            b("help_btn_speed", "sᴘᴇᴇᴅ", "help_speed"),
            b("help_btn_info", "ɪɴғᴏ", "help_info"),
        )
        + _row(
            b("help_btn_playlist", "ᴘʟᴀʏʟɪsᴛ", "help_playlist"),
            b("help_btn_channel", "ᴄʜᴀɴɴᴇʟ", "help_channel"),
        )
    )


def help_menu_kb(lang: Optional[dict] = None) -> str:
    """/help — grid + a Close button (nothing to go 'back' to yet)."""
    return _help_grid(lang) + _row(
        _tg_btn(_lbl(lang, "btn_close", "⌯ ᴄʟᴏsᴇ ⌯"), "close_help", "danger"),
    )


def help_menu_home_kb(lang: Optional[dict] = None) -> str:
    """'show_help' callback (returning to the grid from a category) — grid + Home."""
    return _help_grid(lang) + _row(
        _tg_btn(_lbl(lang, "btn_home", "⌯ ʜᴏᴍᴇ ⌯"), "go_back", random_style()),
    )


def help_back_kb(lang: Optional[dict] = None) -> str:
    """Under every category screen: Back to grid / Close."""
    return (
        _row(_tg_btn(_lbl(lang, "btn_back", "⌯ ʙᴀᴄᴋ ⌯"), "show_help", random_style()))
        + _row(_tg_btn(_lbl(lang, "btn_close", "⌯ ᴄʟᴏsᴇ ⌯"), "close_help", "danger"))
    )


# ═════════════════════════════════════════════════════════════════════════════
# /language
# ═════════════════════════════════════════════════════════════════════════════
def language_kb(
    languages_present: dict,
    current: str,
    row_width: int = 2,
    lang: Optional[dict] = None,
    show_home: bool = False,
) -> str:
    buttons = [
        _tg_btn(
            rich_esc(f"✓ {name}" if code == current else name),
            f"setlang:{code}",
            random_style(),
        )
        for code, name in languages_present.items()
    ]
    html = "".join(
        _row(*buttons[i:i + row_width]) for i in range(0, len(buttons), row_width)
    )
    if show_home:
        html += _row(_tg_btn(_lbl(lang, "btn_home", "⌯ ʜᴏᴍᴇ ⌯"), "go_back", random_style()))
    html += _row(_tg_btn(_lbl(lang, "btn_close", "⌯ ᴄʟᴏsᴇ ⌯"), "close_help", "danger"))
    return html
    

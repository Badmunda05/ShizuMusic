# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------
#
#  Category screens rebuilt to match the reference bot's structure (heading +
#  description + a real Command/Description table + Support/Updates pills +
#  colored Back/Close buttons) — content is ShizuMusic's own commands, taken
#  straight from the old ASCII-box text, just restructured into rich blocks.
# --------------------------------------------------------------------------------

import asyncio
import random

from pyrogram import enums
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

import config
from ShizuMusic import bot, call_py
from ShizuMusic.core.call import leave_vc
from ShizuMusic.core.player import play_song
from ShizuMusic.core.queue import clear_queue, peek_current, pop_current, queue_size
from ShizuMusic.utils.db import is_user_blocked_db
from ShizuMusic.utils.formatters import short
from ShizuMusic.utils.helpers import delete_file
from ShizuMusic.utils.permissions import is_user_authorized
from ShizuMusic.utils.rich_ui import (
    rich_caption,
    rich_details,
    rich_esc,
    rich_heading,
    rich_kv_table,
    rich_note,
    rich_send,
    rich_table,
    rich_edit,
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


def _category_html(title: str, desc: str, rows) -> str:
    """title/desc/rows -> heading + description + Command/Description table + pills."""
    return (
        rich_heading(title, level=3)
        + f"<p>{desc}</p>"
        + rich_table(["ᴄᴏᴍᴍᴀɴᴅ", "ᴅᴇsᴄʀɪᴘᴛɪᴏɴ"], rows)
        + _support_updates_pills()
    )


# ── Help menu layout ───────────────────────────────────────────────────────────
#
#   Row 1 : [ᴧᴅᴍɪɴ]  [ᴧ-ᴘʟᴀʏ]  [ɢ-ᴄᴧsᴛ]
#   Row 2 : [ʙʟ-ᴄʜᴧᴛ] [ʙʟ-ᴜsᴇʀs] [ᴘɪɴɢ]
#   Row 3 : [ᴘʟᴀʏ]   [sᴘᴇᴇᴅ]   [ɪɴғᴏ]
#   Row 4 :          [⌯ ʜᴏᴍᴇ ⌯]
#
# ──────────────────────────────────────────────────────────────────────────────

_HELP_KB = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("ᴧᴅᴍɪɴ",    callback_data="help_admin",    style=enums.ButtonStyle.PRIMARY),
        InlineKeyboardButton("ᴧ-ᴘʟᴀʏ",   callback_data="help_autoplay", style=enums.ButtonStyle.PRIMARY),
        InlineKeyboardButton("ɢ-ᴄᴧsᴛ",   callback_data="help_gcast",    style=enums.ButtonStyle.PRIMARY),
    ],
    [
        InlineKeyboardButton("ʙʟ-ᴄʜᴧᴛ",  callback_data="help_blchat",  style=enums.ButtonStyle.PRIMARY),
        InlineKeyboardButton("ʙʟ-ᴜsᴇʀs", callback_data="help_blusers", style=enums.ButtonStyle.PRIMARY),
        InlineKeyboardButton("ᴘɪɴɢ",     callback_data="help_ping",    style=enums.ButtonStyle.PRIMARY),
    ],
    [
        InlineKeyboardButton("ᴘʟᴀʏ",     callback_data="help_play",  style=enums.ButtonStyle.PRIMARY),
        InlineKeyboardButton("sᴘᴇᴇᴅ",    callback_data="help_speed", style=enums.ButtonStyle.PRIMARY),
        InlineKeyboardButton("ɪɴғᴏ",     callback_data="help_info",  style=enums.ButtonStyle.PRIMARY),
    ],
    [
        InlineKeyboardButton("⌯ ʜᴏᴍᴇ ⌯", callback_data="go_back", style=enums.ButtonStyle.SUCCESS),
    ],
])

# Reference screenshots show BOTH a Back and a Close row under every category
# screen — matched here (Back = blue, Close = red).
_BACK_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("⌯ ʙᴀᴄᴋ ⌯",  callback_data="show_help", style=enums.ButtonStyle.PRIMARY)],
    [InlineKeyboardButton("⌯ ᴄʟᴏsᴇ ⌯", callback_data="close_help", style=enums.ButtonStyle.DANGER)],
])

# ── Help texts ─────────────────────────────────────────────────────────────────
# Same commands/wording as the old ASCII-box version, restructured into a real
# heading + description + Command/Description table.

_HELP_TEXTS = {

    "help_admin": _category_html(
        "⚙️ ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs",
        "ᴄᴏʀᴇ ᴘʟᴀʏʙᴀᴄᴋ ᴄᴏɴᴛʀᴏʟs ғᴏʀ ᴄʜᴀᴛ ᴀᴅᴍɪɴs.",
        [
            ("/pause", "ᴘᴀᴜsᴇ ᴄᴜʀʀᴇɴᴛ ᴘʟᴀʏʙᴀᴄᴋ"),
            ("/resume", "ʀᴇsᴜᴍᴇ ᴘᴀᴜsᴇᴅ ᴘʟᴀʏʙᴀᴄᴋ"),
            ("/skip", "sᴋɪᴘ ᴛᴏ ɴᴇxᴛ sᴏɴɢ"),
            ("/stop, /end", "sᴛᴏᴘ ᴘʟᴀʏʙᴀᴄᴋ &amp; ʟᴇᴀᴠᴇ ᴠᴄ"),
            ("/clear", "ᴄʟᴇᴀʀ ᴀʟʟ sᴏɴɢs ɪɴ ǫᴜᴇᴜᴇ"),
            ("/seek &lt;seconds&gt;", "sᴇᴇᴋ ғᴏʀᴡᴀʀᴅ ʙʏ ɴ sᴇᴄᴏɴᴅs"),
            ("/seekback &lt;seconds&gt;", "sᴇᴇᴋ ʙᴀᴄᴋᴡᴀʀᴅ ʙʏ ɴ sᴇᴄᴏɴᴅs"),
            ("/reboot", "ʀᴇsᴇᴛ ᴄʜᴀᴛ sᴛᴀᴛᴇ &amp; ʟᴇᴀᴠᴇ ᴠᴄ"),
        ],
    ),

    "help_autoplay": _category_html(
        "🔁 ᴀᴜᴛᴏᴘʟᴀʏ ᴄᴏᴍᴍᴀɴᴅs",
        "ᴋᴇᴇᴘ ᴛʜᴇ ǫᴜᴇᴜᴇ ɢᴏɪɴɢ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ʙᴀsᴇᴅ ᴏɴ ᴀ ǫᴜᴇʀʏ.",
        [
            ("/autoplay &lt;query&gt;", "ᴄᴏɴᴛɪɴᴜᴏᴜsʟʏ ᴘʟᴀʏ sᴏɴɢs ʙᴀsᴇᴅ ᴏɴ ʏᴏᴜʀ ǫᴜᴇʀʏ"),
            ("/end, /stop", "sᴛᴏᴘ ᴀᴜᴛᴏᴘʟᴀʏ &amp; ᴄʟᴇᴀʀ ǫᴜᴇᴜᴇ"),
            ("<code>/autoplay sidhu moose wala</code>", "ᴇxᴀᴍᴘʟᴇ"),
            ("<code>/autoplay arijit singh</code>", "ᴇxᴀᴍᴘʟᴇ"),
        ],
    ),

    "help_gcast": _category_html(
        "📢 ɢ-ᴄᴀsᴛ ᴄᴏᴍᴍᴀɴᴅs",
        "ʙʀᴏᴀᴅᴄᴀsᴛ ᴛᴏ ᴇᴠᴇʀʏ sᴇʀᴠᴇᴅ ᴄʜᴀᴛ (ᴏᴡɴᴇʀ ᴏɴʟʏ).",
        [
            ("/broadcast, /gcast", "ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍsɢ ᴏʀ ᴛʏᴘᴇ ᴛᴇxᴛ"),
            ("-pin", "ᴘɪɴ sɪʟᴇɴᴛʟʏ ɪɴ ɢʀᴏᴜᴘs"),
            ("-pinloud", "ᴘɪɴ ᴡɪᴛʜ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ"),
            ("-nogroup", "sᴋɪᴘ ɢʀᴏᴜᴘs"),
            ("-user", "ᴀʟsᴏ sᴇɴᴅ ᴛᴏ ᴜsᴇʀs"),
        ],
    ),

    "help_blchat": _category_html(
        "🚫 ʙʟ-ᴄʜᴀᴛ ᴄᴏᴍᴍᴀɴᴅs",
        "ʙʟᴏᴄᴋ ᴏʀ ᴜɴʙʟᴏᴄᴋ ᴡʜᴏʟᴇ ɢʀᴏᴜᴘs (ᴏᴡɴᴇʀ ᴏɴʟʏ).",
        [
            ("/gblock", "ʙʟᴏᴄᴋ ᴄᴜʀʀᴇɴᴛ ɢʀᴏᴜᴘ — ɴᴏ ᴄᴏᴍᴍᴀɴᴅs ᴡɪʟʟ ᴡᴏʀᴋ"),
            ("/gblock &lt;-100xxxxxxx&gt;", "ʙʟᴏᴄᴋ ʙʏ ᴄʜᴀᴛ ɪᴅ"),
            ("/gunblock", "ᴜɴʙʟᴏᴄᴋ ɢʀᴏᴜᴘ"),
            ("/gunblock &lt;-100xxxxxxx&gt;", "ᴜɴʙʟᴏᴄᴋ ʙʏ ᴄʜᴀᴛ ɪᴅ"),
            ("/blocklist", "sʜᴏᴡ ᴀʟʟ ʙʟᴏᴄᴋᴇᴅ ɢʀᴏᴜᴘs &amp; ᴜsᴇʀs"),
        ],
    ),

    "help_blusers": _category_html(
        "🚫 ʙʟ-ᴜsᴇʀs ᴄᴏᴍᴍᴀɴᴅs",
        "ʙʟᴏᴄᴋ ᴏʀ ᴜɴʙʟᴏᴄᴋ ɪɴᴅɪᴠɪᴅᴜᴀʟ ᴜsᴇʀs (ᴏᴡɴᴇʀ ᴏɴʟʏ).",
        [
            ("/ublock", "ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ's ᴍsɢ ᴛᴏ ʙʟᴏᴄᴋ — ᴛʜᴇʏ ᴄᴀɴ'ᴛ ᴜsᴇ ᴀɴʏ ᴄᴏᴍᴍᴀɴᴅ"),
            ("/ublock &lt;user id&gt;", "ʙʟᴏᴄᴋ ʙʏ ᴜsᴇʀ ɪᴅ"),
            ("/uunblock", "ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ's ᴍsɢ ᴛᴏ ᴜɴʙʟᴏᴄᴋ"),
            ("/uunblock &lt;user id&gt;", "ᴜɴʙʟᴏᴄᴋ ʙʏ ᴜsᴇʀ ɪᴅ"),
            ("/blocklist", "sʜᴏᴡ ᴀʟʟ ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs &amp; ᴄʜᴀᴛs"),
        ],
    ),

    "help_ping": _category_html(
        "🏓 ᴘɪɴɢ ᴄᴏᴍᴍᴀɴᴅs",
        "ʟᴀᴛᴇɴᴄʏ ᴀɴᴅ sʏsᴛᴇᴍ ᴅɪᴀɢɴᴏsᴛɪᴄs.",
        [
            ("/ping", "ʙᴏᴛ ʟᴀᴛᴇɴᴄʏ, ʀᴀᴍ, ᴄᴘᴜ, ᴅɪsᴋ &amp; ᴜᴘᴛɪᴍᴇ sᴛᴀᴛs"),
            ("/speedtest, /spt", "ɴᴇᴛᴡᴏʀᴋ sᴘᴇᴇᴅ ᴛᴇsᴛ (ᴏᴡɴᴇʀ ᴏɴʟʏ)"),
            ("/stats", "ғᴜʟʟ sʏsᴛᴇᴍ + ᴍᴏɴɢᴏᴅʙ sᴛᴀᴛs (ᴏᴡɴᴇʀ ᴏɴʟʏ)"),
        ],
    ),

    "help_play": _category_html(
        "🎵 ᴘʟᴀʏ ᴄᴏᴍᴍᴀɴᴅs",
        "sᴛᴀʀᴛ ᴀᴜᴅɪᴏ ᴏʀ ᴠɪᴅᴇᴏ ᴘʟᴀʏʙᴀᴄᴋ ɪɴ ᴀ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ.",
        [
            ("/play &lt;song name or URL&gt;", "ᴘʟᴀʏ ᴀᴜᴅɪᴏ ɪɴ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ"),
            ("/vplay &lt;song name or URL&gt;", "ᴘʟᴀʏ ᴠɪᴅᴇᴏ ɪɴ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ"),
            ("ʀᴇᴘʟʏ ᴛᴏ ᴀᴜᴅɪᴏ/ᴠɪᴅᴇᴏ + /play", "ᴘʟᴀʏ ᴛʜᴀᴛ ᴍᴇᴅɪᴀ ᴅɪʀᴇᴄᴛʟʏ"),
            ("ʏᴏᴜᴛᴜʙᴇ ᴜʀʟs", "sᴜᴘᴘᴏʀᴛᴇᴅ"),
            ("ᴍᴀx ᴅᴜʀᴀᴛɪᴏɴ", f"{config.MAX_DURATION_SECONDS // 60} ᴍɪɴᴜᴛᴇs"),
            ("ǫᴜᴇᴜᴇ ʟɪᴍɪᴛ", f"{config.QUEUE_LIMIT} sᴏɴɢs"),
        ],
    ),

    "help_speed": _category_html(
        "🎚️ sᴘᴇᴇᴅ &amp; ᴇғғᴇᴄᴛs",
        "ᴀᴅᴊᴜsᴛ ᴘʟᴀʏʙᴀᴄᴋ sᴘᴇᴇᴅ ᴀɴᴅ ᴀᴜᴅɪᴏ ᴇғғᴇᴄᴛs.",
        [
            ("/speed &lt;0.25–4.0&gt;", "ᴄʜᴀɴɢᴇ ᴘʟᴀʏʙᴀᴄᴋ sᴘᴇᴇᴅ — ᴇ.ɢ. /speed 1.5"),
            ("/speedreset", "ʀᴇsᴇᴛ sᴘᴇᴇᴅ ᴛᴏ ɴᴏʀᴍᴀʟ (1.0x)"),
            ("/bass &lt;1–20&gt;", "ʙᴏᴏsᴛ ʙᴀss ʙʏ ɴ ᴅʙ — ᴇ.ɢ. /bass 10"),
            ("/bassoff", "ᴛᴜʀɴ ᴏғғ ʙᴀss ʙᴏᴏsᴛ"),
            ("/effecton", "ᴀᴘᴘʟʏ ᴇғғᴇᴄᴛs ᴛᴏ ᴀʟʟ sᴏɴɢs"),
            ("/effectoff", "ᴅɪsᴀʙʟᴇ ᴀᴜᴛᴏ ᴇғғᴇᴄᴛs"),
            ("/effects", "sʜᴏᴡ ᴄᴜʀʀᴇɴᴛ ᴇғғᴇᴄᴛ sᴛᴀᴛᴜs"),
        ],
    ),

    "help_info": _category_html(
        "ℹ️ ɪɴғᴏ ᴄᴏᴍᴍᴀɴᴅs",
        "ʙᴏᴛ, ᴄʜᴀᴛ, ᴀɴᴅ ᴜsᴇʀ ɪɴғᴏʀᴍᴀᴛɪᴏɴ.",
        [
            ("/id", "ɢᴇᴛ ɪᴅs ᴏғ ᴜsᴇʀ / ᴄʜᴀᴛ / ᴍsɢ — ᴀʟsᴏ ᴡᴏʀᴋs ᴡɪᴛʜ ʀᴇᴘʟʏ"),
            ("/id @username", "ɢᴇᴛ ᴀɴʏ ᴜsᴇʀ's ɪᴅ"),
            ("/repo", "sᴏᴜʀᴄᴇ ᴄᴏᴅᴇ ʟɪɴᴋ"),
            ("/stats", "ғᴜʟʟ sᴛᴀᴛs — sʏsᴛᴇᴍ + ᴍᴏɴɢᴏᴅʙ ɪɴғᴏ (ᴏᴡɴᴇʀ ᴏɴʟʏ)"),
        ],
    ),
}


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN CALLBACK HANDLER
# ══════════════════════════════════════════════════════════════════════════════

@bot.on_callback_query()
async def on_callback(client, cbq: CallbackQuery) -> None:

    chat_id = cbq.message.chat.id
    user    = cbq.from_user
    data    = cbq.data

    # ── Block check ────────────────────────────────────────────────────────────
    if user and is_user_blocked_db(user.id):
        await cbq.answer()
        return

    # ── Admin check for playback controls ─────────────────────────────────────
    if data in ("pause", "resume", "skip", "stop", "clear"):
        if not await is_user_authorized(cbq):
            await cbq.answer("❍ ᴀᴅᴍɪɴs ᴏɴʟʏ", show_alert=True)
            return

    # ── PAUSE ──────────────────────────────────────────────────────────────────
    if data == "pause":
        try:
            await call_py.pause(chat_id)
            await cbq.answer("Paused")
            await rich_send(
                bot, chat_id,
                rich_heading("⏸ ˢᵗʳᵉᵃᵐ ᴘᴀᴜsᴇᴅ", level=3)
                + rich_note(f"❍ ʙʏ » {user.mention}"),
            )
        except Exception:
            await cbq.answer("Failed To Pause", show_alert=True)

    # ── RESUME ─────────────────────────────────────────────────────────────────
    elif data == "resume":
        try:
            await call_py.resume(chat_id)
            await cbq.answer("Resumed")
            await rich_send(
                bot, chat_id,
                rich_heading("▶ sᴛʀᴇᴀᴍ ʀᴇsᴜᴍᴇᴅ", level=3)
                + rich_note(f"❍ ʙʏ » {user.mention}"),
            )
        except Exception:
            await cbq.answer("Failed To Resume", show_alert=True)

    # ── SKIP ───────────────────────────────────────────────────────────────────
    elif data == "skip":
        if not queue_size(chat_id):
            await cbq.answer("Queue Is Empty", show_alert=True)
            return

        skipped = pop_current(chat_id)

        try:
            await call_py.leave_call(chat_id)
        except Exception:
            pass

        await asyncio.sleep(2)

        try:
            delete_file(skipped.get("file_path", ""))
        except Exception:
            pass

        await rich_send(
            bot, chat_id,
            rich_heading("⏭ ᴛʀᴀᴄᴋ sᴋɪᴘᴘᴇᴅ", level=3)
            + rich_kv_table([
                ("ʙʏ", rich_esc(user.mention)),
                ("sᴏɴɢ", f"<code>{rich_esc(short(skipped['title']))}</code>"),
            ]),
        )

        nxt = peek_current(chat_id)
        if nxt:
            await cbq.answer("Playing Next")
            dm = await bot.send_message(
                chat_id,
                f"<b>❍ ɴᴇxᴛ ᴛʀᴀᴄᴋ :</b> <code>{nxt['title']}</code>",
                parse_mode=ParseMode.HTML,
            )
            await play_song(chat_id, dm, nxt)
        else:
            await cbq.answer("Queue Empty", show_alert=True)

    # ── STOP ───────────────────────────────────────────────────────────────────
    elif data == "stop":
        await leave_vc(chat_id)
        await cbq.answer("Stopped")
        await rich_send(
            bot, chat_id,
            rich_heading("⏹ ᴘʟᴀʏʙᴀᴄᴋ sᴛᴏᴘᴘᴇᴅ", level=3)
            + rich_note(f"❍ ʙʏ » {user.mention}"),
        )

    # ── CLEAR ──────────────────────────────────────────────────────────────────
    elif data == "clear":
        clear_queue(chat_id)
        await cbq.answer("Queue Cleared")
        await rich_edit(
            cbq.message,
            rich_heading("🧹 ǫᴜᴇᴜᴇ ᴄʟᴇᴀʀᴇᴅ", level=3)
            + rich_note(f"❍ ʙʏ » {user.mention}"),
        )

    # ── NOOP ───────────────────────────────────────────────────────────────────
    elif data == "noop":
        await cbq.answer()

    # ── CLOSE HELP ─────────────────────────────────────────────────────────────
    elif data == "close_help":
        await cbq.answer()
        try:
            await cbq.message.delete()
        except Exception:
            pass

    # ── HELP ───────────────────────────────────────────────────────────────────
    elif data == "show_help":
        await cbq.answer()
        heading = rich_heading("📜 ᴄʜᴏᴏsᴇ ᴀ ᴄᴀᴛᴇɢᴏʀʏ", level=3)
        if getattr(cbq.message, "photo", None):
            # /start's message is a photo — can't edit its caption into a
            # true rich message, so swap it out for one.
            try:
                await cbq.message.delete()
            except Exception:
                pass
            await rich_send(bot, chat_id, heading, reply_markup=_HELP_KB)
        else:
            await rich_edit(cbq.message, heading, reply_markup=_HELP_KB)

    elif data == "go_back":
        await _go_back(cbq)

    elif data.startswith("help_"):
        await cbq.answer()
        text = _HELP_TEXTS.get(data)
        if text:
            await rich_edit(cbq.message, text, reply_markup=_BACK_KB)


# ── Go back to start message ───────────────────────────────────────────────────

async def _go_back(cbq: CallbackQuery) -> None:
    await cbq.answer()
    uid  = cbq.from_user.id
    name = cbq.from_user.first_name or "User"

    caption = (
            f"<p>❍ ʜᴇʏ <a href='tg://user?id={uid}'>{rich_esc(name)}</a>, "
            "ᴡᴇʟᴄᴏᴍᴇ ᴀʙᴏᴀʀᴅ! 🎶</p>"
            + f"<p>ɪ ᴀᴍ <b>{rich_esc(config.BOT_NAME)}</b> — ᴀ ғᴀsᴛ &amp; "
              "ᴘᴏᴡᴇʀғᴜʟ ᴛᴇʟᴇɢʀᴀᴍ ᴍᴜsɪᴄ ᴘʟᴀʏᴇʀ ʙᴏᴛ ᴡɪᴛʜ sᴏᴍᴇ ᴀᴡᴇsᴏᴍᴇ "
              "ғᴇᴀᴛᴜʀᴇs.</p>"
            + rich_details(
                "✦ ᴋᴇʏ ғᴇᴀᴛᴜʀᴇs ✦",
                rich_table(
                    ["ғᴇᴀᴛᴜʀᴇ", "ᴅᴇᴛᴀɪʟs"],
                    [
                        ("🎵 sᴛʀᴇᴀᴍɪɴɢ", "ᴘʟᴀʏ ᴀᴜᴅɪᴏ &amp; ᴠɪᴅᴇᴏ ɪɴ ᴠᴏɪᴄᴇ ᴄʜᴀᴛs"),
                        ("🔁 ᴀᴜᴛᴏᴘʟᴀʏ", "ᴋᴇᴇᴘs ᴛʜᴇ ǫᴜᴇᴜᴇ ɢᴏɪɴɢ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ"),
                        ("🎚️ ᴇғғᴇᴄᴛs", "sᴘᴇᴇᴅ ᴄᴏɴᴛʀᴏʟ &amp; ʙᴀss ʙᴏᴏsᴛ"),
                        ("🛡️ ᴍᴏᴅᴇʀᴀᴛɪᴏɴ", "ʙʟᴏᴄᴋ/ᴜɴʙʟᴏᴄᴋ ᴄʜᴀᴛs &amp; ᴜsᴇʀs"),
                    ],
                ),
                open=True,
            )
            + rich_details(
                "✧ ᴡʜʏ ᴄʜᴏᴏsᴇ ɪᴛ? ✧",
                "<p>⭐ sɪᴍᴘʟᴇ sʟᴀsʜ ᴄᴏᴍᴍᴀɴᴅs, ɴᴏ sᴇᴛᴜᴘ ɴᴇᴇᴅᴇᴅ.</p>"
                "<p>🎧 ᴄʟᴇᴀɴ, ʟᴏᴡ-ʟᴀɢ sᴛʀᴇᴀᴍɪɴɢ.</p>"
                "<p>❍ ᴄʟɪᴄᴋ ʜᴇʟᴘ ʙᴇʟᴏᴡ ғᴏʀ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs.</p>",
                open=True,
            )
            + rich_note(f"ᴘᴏᴡᴇʀᴇᴅ ʙʏ » <a href='https://t.me/PBXCHATS'>sʜɪᴢᴜ-ᴍᴜsɪᴄ™</a>")
            + _support_updates_pills()
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⛩️ ᴧᴅᴅ мᴇ ʙᴧʙʏ ⛩️",
                              url=f"{config.BOT_LINK}?startgroup=true",
                              style=enums.ButtonStyle.PRIMARY)],
        [
            InlineKeyboardButton("🍬 sᴜᴘᴘᴏʀᴛ 🍬", url=config.SUPPORT_GROUP,
                                 style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("🍹 ᴜᴘᴅᴀᴛᴇs 🍹",  url=config.UPDATES_CHANNEL,
                                 style=enums.ButtonStyle.SUCCESS),
        ],
        [InlineKeyboardButton("🏩 ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs 🏩",
                              callback_data="show_help",
                              style=enums.ButtonStyle.PRIMARY)],
        [
            InlineKeyboardButton("🫧 ᴏᴡɴᴇʀ 🫧",
                                 url=f"tg://user?id={config.OWNER_ID}",
                                 style=enums.ButtonStyle.DEFAULT),
            InlineKeyboardButton("🍡 sᴏᴜʀᴄᴇ 🍡",
                                 url="https://github.com/Badmunda05/ShizuMusic/fork",
                                 style=enums.ButtonStyle.DEFAULT),
        ],
    ])

    photo = random.choice(config.START_PHOTOS)
    chat_id = cbq.message.chat.id

    try:
        await cbq.message.delete()
    except Exception:
        pass

    try:
        await bot.send_photo(
            chat_id,
            photo,
            caption=rich_caption(caption),
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
    except Exception:
        await rich_send(bot, chat_id, caption, reply_markup=kb)


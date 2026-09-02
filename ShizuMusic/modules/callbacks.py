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
from ShizuMusic.utils.rich_ui import rich_edit, rich_esc, rich_heading, rich_table


def _support_updates_pills() -> str:
    return (
        "<p>"
        f'<tg-button type="url" style="primary" url="{config.SUPPORT_GROUP}">'
        "🍬 Support</tg-button> "
        f'<tg-button type="url" style="success" url="{config.UPDATES_CHANNEL}">'
        "🍹 Updates</tg-button>"
        "</p>"
    )


def _category_html(title: str, desc: str, rows) -> str:
    """title/desc/rows -> heading + description + Command/Description table + pills."""
    return (
        rich_heading(title, level=3)
        + f"<p>{desc}</p>"
        + rich_table(["Command", "Description"], rows)
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
        "⚙️ Admin Commands",
        "Core playback controls for chat admins.",
        [
            ("/pause", "Pause current playback"),
            ("/resume", "Resume paused playback"),
            ("/skip", "Skip to next song"),
            ("/stop, /end", "Stop playback &amp; leave VC"),
            ("/clear", "Clear all songs in queue"),
            ("/seek &lt;seconds&gt;", "Seek forward by n seconds"),
            ("/seekback &lt;seconds&gt;", "Seek backward by n seconds"),
            ("/reboot", "Reset chat state &amp; leave VC"),
        ],
    ),

    "help_autoplay": _category_html(
        "🔁 Autoplay Commands",
        "Keep the queue going automatically based on a query.",
        [
            ("/autoplay &lt;query&gt;", "Continuously play songs based on your query"),
            ("/end, /stop", "Stop autoplay &amp; clear queue"),
            ("<code>/autoplay sidhu moose wala</code>", "Example"),
            ("<code>/autoplay arijit singh</code>", "Example"),
        ],
    ),

    "help_gcast": _category_html(
        "📢 G-Cast Commands",
        "Broadcast to every served chat (owner only).",
        [
            ("/broadcast, /gcast", "Reply to a msg or type text"),
            ("-pin", "Pin silently in groups"),
            ("-pinloud", "Pin with notification"),
            ("-nogroup", "Skip groups"),
            ("-user", "Also send to users"),
        ],
    ),

    "help_blchat": _category_html(
        "🚫 Bl-Chat Commands",
        "Block or unblock whole groups (owner only).",
        [
            ("/gblock", "Block current group — no commands will work"),
            ("/gblock &lt;-100xxxxxxx&gt;", "Block by chat id"),
            ("/gunblock", "Unblock group"),
            ("/gunblock &lt;-100xxxxxxx&gt;", "Unblock by chat id"),
            ("/blocklist", "Show all blocked groups &amp; users"),
        ],
    ),

    "help_blusers": _category_html(
        "🚫 Bl-Users Commands",
        "Block or unblock individual users (owner only).",
        [
            ("/ublock", "Reply to a user's msg to block — they can't use any command"),
            ("/ublock &lt;user id&gt;", "Block by user id"),
            ("/uunblock", "Reply to a user's msg to unblock"),
            ("/uunblock &lt;user id&gt;", "Unblock by user id"),
            ("/blocklist", "Show all blocked users &amp; chats"),
        ],
    ),

    "help_ping": _category_html(
        "🏓 Ping Commands",
        "Latency and system diagnostics.",
        [
            ("/ping", "Bot latency, RAM, CPU, disk &amp; uptime stats"),
            ("/speedtest, /spt", "Network speed test (owner only)"),
            ("/stats", "Full system + MongoDB stats (owner only)"),
        ],
    ),

    "help_play": _category_html(
        "🎵 Play Commands",
        "Start audio or video playback in a voice chat.",
        [
            ("/play &lt;song name or URL&gt;", "Play audio in voice chat"),
            ("/vplay &lt;song name or URL&gt;", "Play video in voice chat"),
            ("Reply to audio/video + /play", "Play that media directly"),
            ("YouTube URLs", "Supported"),
            ("Max duration", f"{config.MAX_DURATION_SECONDS // 60} minutes"),
            ("Queue limit", f"{config.QUEUE_LIMIT} songs"),
        ],
    ),

    "help_speed": _category_html(
        "🎚️ Speed &amp; Effects",
        "Adjust playback speed and audio effects.",
        [
            ("/speed &lt;0.25–4.0&gt;", "Change playback speed — e.g. /speed 1.5"),
            ("/speedreset", "Reset speed to normal (1.0x)"),
            ("/bass &lt;1–20&gt;", "Boost bass by n dB — e.g. /bass 10"),
            ("/bassoff", "Turn off bass boost"),
            ("/effecton", "Apply effects to all songs"),
            ("/effectoff", "Disable auto effects"),
            ("/effects", "Show current effect status"),
        ],
    ),

    "help_info": _category_html(
        "ℹ️ Info Commands",
        "Bot, chat, and user information.",
        [
            ("/id", "Get IDs of user / chat / msg — also works with reply"),
            ("/id @username", "Get any user's id"),
            ("/repo", "Source code link"),
            ("/stats", "Full stats — system + MongoDB info (owner only)"),
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
            await client.send_message(
                chat_id,
                f"<b>❍ sᴛʀᴇᴀᴍ ᴘᴀᴜsᴇᴅ</b>\n<b>❍ ʙʏ :</b> {user.mention}",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            await cbq.answer("Failed To Pause", show_alert=True)

    # ── RESUME ─────────────────────────────────────────────────────────────────
    elif data == "resume":
        try:
            await call_py.resume(chat_id)
            await cbq.answer("Resumed")
            await client.send_message(
                chat_id,
                f"<b>❍ sᴛʀᴇᴀᴍ ʀᴇsᴜᴍᴇᴅ</b>\n<b>❍ ʙʏ :</b> {user.mention}",
                parse_mode=ParseMode.HTML,
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

        await client.send_message(
            chat_id,
            f"<b>❍ ᴛʀᴀᴄᴋ sᴋɪᴩᴩᴇᴅ</b>\n"
            f"<b>❍ ʙʏ :</b> {user.mention}\n"
            f"<b>❍ sᴏɴɢ :</b> <code>{short(skipped['title'])}</code>",
            parse_mode=ParseMode.HTML,
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
        await client.send_message(
            chat_id,
            f"<b>❍ ᴘʟᴀʏʙᴀᴄᴋ sᴛᴏᴘᴘᴇᴅ</b>\n<b>❍ ʙʏ :</b> {user.mention}",
            parse_mode=ParseMode.HTML,
        )

    # ── CLEAR ──────────────────────────────────────────────────────────────────
    elif data == "clear":
        clear_queue(chat_id)
        await cbq.answer("Queue Cleared")
        await cbq.message.edit_text(
            f"<b>❍ ǫᴜᴇᴜᴇ ᴄʟᴇᴀʀᴇᴅ</b>\n<b>❍ ʙʏ :</b> {user.mention}",
            parse_mode=ParseMode.HTML,
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
        await rich_edit(
            cbq.message,
            rich_heading("📜 Choose a category", level=3),
            reply_markup=_HELP_KB,
        )

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
        f"<p>❍ Hey <a href='tg://user?id={uid}'>{rich_esc(name)}</a>, "
        f"this is <b>{rich_esc(config.BOT_NAME)}</b> — a fast &amp; powerful "
        "Telegram music bot.</p>"
        + _support_updates_pills()
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⛩️ ᴧᴅᴅ мᴇ ʙᴧʙʏ ⛩️",
                              url=f"{config.BOT_LINK}?startgroup=true",
                              style=enums.ButtonStyle.PRIMARY)],
        [
            InlineKeyboardButton("🍬 sᴜᴩᴩᴏʀᴛ 🍬", url=config.SUPPORT_GROUP,
                                 style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("🍹 ᴜᴩᴅᴀᴛᴇ 🍹",  url=config.UPDATES_CHANNEL,
                                 style=enums.ButtonStyle.SUCCESS),
        ],
        [InlineKeyboardButton("🏩 ʜᴇʟᴩ ᴧɴᴅ ᴄᴏᴍᴍᴀɴᴅs 🏩",
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

    await rich_edit(cbq.message, caption, reply_markup=kb)

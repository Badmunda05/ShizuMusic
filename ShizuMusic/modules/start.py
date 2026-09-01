# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------
#
#  Polished against nub-music-bot's plugins/start.py (Bot API 10.2+ Rich
#  Messages) pattern: rich_heading / rich_table / rich_kv_table / rich_button
#  instead of plain ASCII-box text. Deliberately NOT copied from that repo:
#    - EmojiTag / <tg-emoji> premium custom emoji ids — plain unicode emoji
#      only, as requested.
#    - Its Buttons/Messages classes, playlist deep-links, sudoers/lang system
#      — ShizuMusic doesn't have those subsystems, so start.py stays self
#      contained instead of inventing dependencies that don't exist here.
#  callback_data values (show_help / close_help / help_admin / help_autoplay /
#  help_gcast / help_blchat / help_blusers / help_ping / help_play /
#  help_speed / help_info) are unchanged so ShizuMusic/modules/callbacks.py
#  keeps working exactly as it already does — this file only touches how the
#  /start and /help *entry* screens look, not the per-category screens.
# --------------------------------------------------------------------------------

import random

from pyrogram import filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from ShizuMusic import bot
from config import START_ANIMATIONS
from ShizuMusic.modules.block import user_allowed
from ShizuMusic.utils.db import add_broadcast_chat, add_served_chat, add_served_user
from ShizuMusic.utils.rich_ui import (
    RICH_AVAILABLE,
    rich_button,
    rich_details,
    rich_esc,
    rich_heading,
    rich_kv_table,
    rich_note,
    rich_reply,
    rich_send,
    rich_table,
)

# ── Message effect IDs (Telegram premium effects) ─────────────────────────────
EFFECT_ID = [
    5046509860389126442,
    5107584321108051014,
    5104841245755180586,
    5159385139981059251,
]

# Plain-text short caption for the animation itself — captions can't be rich.
_ANIMATION_CAPTION = "🥀 sʜɪᴢᴜ-ᴍᴜsɪᴄ™"

_HELP_CATEGORIES = [
    ("🛡", "Admin", "help_admin", "Auth, blocklist & moderation"),
    ("🔁", "Autoplay", "help_autoplay", "Keep the queue never empty"),
    ("📢", "G-Cast", "help_gcast", "Broadcast to every served chat"),
    ("🚫", "Bl-Chat", "help_blchat", "Block/unblock a whole group"),
    ("👤", "Bl-Users", "help_blusers", "Block/unblock a single user"),
    ("🏓", "Ping", "help_ping", "Latency & speedtest"),
    ("▶️", "Play", "help_play", "Play, skip, pause, seek…"),
    ("⚡", "Speed", "help_speed", "Playback speed & effects"),
    ("ℹ️", "Info", "help_info", "Repo, chat/user id lookups"),
]


# ── shared builders ─────────────────────────────────────────────────────────

def _welcome_html(uid: int, name: str) -> str:
    return (
        rich_heading(f"Hey {rich_esc(name)} 🥀", level=3)
        + f"<p>This is <b>{rich_esc(config.BOT_NAME)}</b> — a fast &amp; powerful "
          "Telegram music player bot.</p>"
        + rich_details(
            "🎧 What can I do?",
            "<p>Play music in group voice chats from YouTube, Spotify, and "
            "more. Tap <b>Help</b> below for the full command list.</p>",
            open=True,
        )
        + rich_note(f"Powered by <a href='https://t.me/PBXCHATS'>sʜɪᴢᴜ-ᴍᴜsɪᴄ™</a>")
    )


def _welcome_buttons_html() -> str:
    row1 = rich_button("⛩️ Add me baby", url=f"{config.BOT_LINK}?startgroup=true", style="success")
    row2 = " ".join([
        rich_button("🍬 Support", url=config.SUPPORT_GROUP),
        rich_button("🍹 Updates", url=config.UPDATES_CHANNEL),
    ])
    row3 = rich_button("📖 Help & Commands", callback_data="show_help", style="primary")
    row4 = " ".join([
        rich_button("🫧 Owner", url=f"tg://user?id={config.OWNER_ID}"),
        rich_button("🍡 Source", url="https://github.com/Badmunda05/ShizuMusic/fork"),
    ])
    return f"<p>{row1}<br/>{row2}<br/>{row3}<br/>{row4}</p>"


def _help_entry_html() -> str:
    """Category picker shown on `/help` and via the `show_help`/`close-help-back` callback."""
    rows = [(f"{emoji} <b>{title}</b>", desc) for emoji, title, _, desc in _HELP_CATEGORIES]
    table = rich_table(["Category", "What's inside"], rows)
    buttons = "".join(
        "<p>" + " ".join(
            rich_button(f"{emoji} {title}", callback_data=cb)
            for emoji, title, cb, _ in _HELP_CATEGORIES[i:i + 3]
        ) + "</p>"
        for i in range(0, len(_HELP_CATEGORIES), 3)
    )
    buttons += f"<p>{rich_button('⌯ Close ⌯', callback_data='close_help', style='danger')}</p>"

    return (
        rich_heading("📜 Choose a category", level=3)
        + table
        + buttons
        + rich_note(f"Powered by <a href='https://t.me/PBXCHATS'>sʜɪᴢᴜ-ᴍᴜsɪᴄ™</a>")
    )


def _new_user_log_html(user) -> str:
    return rich_heading("🆕 New user started the bot", level=2) + rich_kv_table([
        ("👤 Name", rich_esc(user.first_name)),
        ("🔗 Username", f"@{rich_esc(user.username)}" if user.username else "<i>None</i>"),
        ("🔑 User ID", f"<code>{user.id}</code>"),
        ("⭐ Premium", "Yes" if getattr(user, "is_premium", False) else "No"),
    ])


def _new_group_log_html(chat, added_by_name) -> str:
    return rich_heading("➕ Bot added to a new group", level=2) + rich_kv_table([
        ("📌 Title", rich_esc(chat.title or "Unknown")),
        ("🔑 Chat ID", f"<code>{chat.id}</code>"),
        ("👤 Added by", rich_esc(added_by_name)),
    ])


# ── classic (guaranteed-working) fallbacks, unchanged from before ───────────

def _classic_start_private(uid, name):
    caption = (
        "<b>╭────────────────────▣</b>\n"
        f"<b>│❍ ʜᴇʏ</b> <a href='tg://user?id={uid}'>{name}</a>, 🥀\n"
        f"<b>│❍ ᴛʜɪs ɪs {config.BOT_NAME} !</b>\n"
        "<b>├────────────────────▣</b>\n"
        "<b>│❍ ᴀ ғᴀsᴛ & ᴘᴏᴡᴇʀғᴜʟ ᴛᴇʟᴇɢʀᴀᴍ</b>\n"
        "<b>│ ᴍᴜsɪᴄ ᴘʟᴀʏᴇʀ ʙᴏᴛ ᴡɪᴛʜ</b>\n"
        "<b>│ sᴏᴍᴇ ᴀᴡᴇsᴏᴍᴇ ғᴇᴀᴛᴜʀᴇs.</b>\n"
        "<b>├────────────────────▣</b>\n"
        "<b>│❍ ᴄʟɪᴄᴋ ʜᴇʟᴘ ғᴏʀ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs.</b>\n"
        "<b>├────────────────────▣</b>\n"
        f"<b>│❍ ᴘᴏᴡᴇʀᴇᴅ ʙʏ » "
        f"<a href='https://t.me/PBXCHATS'>sʜɪᴢᴜ-ᴍᴜsɪᴄ™</a></b>\n"
        "<b>╰────────────────────▣</b>"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⛩️ ᴧᴅᴅ мᴇ ʙᴧʙʏ ⛩️",
                              url=f"{config.BOT_LINK}?startgroup=true")],
        [
            InlineKeyboardButton("🍬 sᴜᴘᴘᴏʀᴛ 🍬", url=config.SUPPORT_GROUP),
            InlineKeyboardButton("🍹 ᴜᴘᴅᴀᴛᴇs 🍹",  url=config.UPDATES_CHANNEL),
        ],
        [InlineKeyboardButton("🏩 ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs 🏩",
                              callback_data="show_help")],
        [
            InlineKeyboardButton("🫧 ᴏᴡɴᴇʀ 🫧",
                                 url=f"tg://user?id={config.OWNER_ID}"),
            InlineKeyboardButton("🍡 sᴏᴜʀᴄᴇ 🍡",
                                 url="https://github.com/Badmunda05/ShizuMusic/fork"),
        ],
    ])
    return caption, kb


def _classic_help_entry(uid, name):
    caption = (
        "<b>╭────────────────────▣</b>\n"
        f"<b>│❍ ʜᴇʏ</b> <a href='tg://user?id={uid}'>{name}</a>, 🥀\n"
        "<b>├────────────────────▣</b>\n"
        "<b>│📜 ᴄʜᴏᴏsᴇ ᴀ ᴄᴀᴛᴇɢᴏʀʏ :</b>\n"
        "<b>├────────────────────▣</b>\n"
        f"<b>│❍ ᴘᴏᴡᴇʀᴇᴅ ʙʏ » "
        f"<a href='https://t.me/PBXCHATS'>sʜɪᴢᴜ-ᴍᴜsɪᴄ™</a></b>\n"
        "<b>╰────────────────────▣</b>"
    )
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ᴧᴅᴍɪɴ",    callback_data="help_admin"),
            InlineKeyboardButton("ᴧ-ᴘʟᴀʏ",   callback_data="help_autoplay"),
            InlineKeyboardButton("ɢ-ᴄᴧsᴛ",   callback_data="help_gcast"),
        ],
        [
            InlineKeyboardButton("ʙʟ-ᴄʜᴧᴛ",  callback_data="help_blchat"),
            InlineKeyboardButton("ʙʟ-ᴜsᴇʀs", callback_data="help_blusers"),
            InlineKeyboardButton("ᴘɪɴɢ",     callback_data="help_ping"),
        ],
        [
            InlineKeyboardButton("ᴘʟᴀʏ",     callback_data="help_play"),
            InlineKeyboardButton("sᴘᴇᴇᴅ",    callback_data="help_speed"),
            InlineKeyboardButton("ɪɴғᴏ",     callback_data="help_info"),
        ],
        [InlineKeyboardButton("⌯ ᴄʟᴏsᴇ ⌯", callback_data="close_help")],
    ])
    return caption, kb


# ── /start ────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("start") & user_allowed)
async def start_handler(_, message: Message) -> None:

    uid       = message.from_user.id
    name      = message.from_user.first_name or "User"
    chat_id   = message.chat.id
    chat_type = message.chat.type
    animation = random.choice(START_ANIMATIONS)

    # ── Delete the user's /start command message ──────────────────────────────
    try:
        await message.delete()
    except Exception:
        pass

    try:
        add_served_user(uid)
        add_served_chat(chat_id)
    except Exception:
        pass

    # ── Private ───────────────────────────────────────────────────────────────
    if chat_type == ChatType.PRIVATE:

        if RICH_AVAILABLE:
            try:
                await message.reply_animation(
                    animation,
                    caption=_ANIMATION_CAPTION,
                    message_effect_id=random.choice(EFFECT_ID),
                )
            except Exception:
                pass
            sent = await rich_reply(
                message, _welcome_html(uid, name) + _welcome_buttons_html(), quote=False
            )
        else:
            classic_caption, classic_kb = _classic_start_private(uid, name)
            sent = await message.reply_animation(
                animation,
                caption=classic_caption,
                parse_mode=ParseMode.HTML,
                reply_markup=classic_kb,
                message_effect_id=random.choice(EFFECT_ID),
            )

        try:
            add_broadcast_chat(chat_id, "private")
        except Exception:
            pass

        if config.LOGGER_ID:
            try:
                if RICH_AVAILABLE:
                    await rich_send(bot, config.LOGGER_ID, _new_user_log_html(message.from_user))
                else:
                    await bot.send_message(
                        config.LOGGER_ID,
                        "<b>#ɴᴇᴡᴜsᴇʀ sᴛᴀʀᴛᴇᴅ</b>\n\n"
                        f"<b>❍ ɴᴀᴍᴇ     :</b> <a href='tg://user?id={uid}'>{name}</a>\n"
                        f"<b>❍ ɪᴅ       :</b> <code>{uid}</code>\n"
                        f"<b>❍ ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username or 'N/A'}",
                        parse_mode=ParseMode.HTML,
                    )
            except Exception:
                pass

    # ── Group ─────────────────────────────────────────────────────────────────
    else:
        chat_title = message.chat.title or "ᴛʜɪs ᴄʜᴀᴛ"

        if RICH_AVAILABLE:
            try:
                await message.reply_animation(animation, caption=_ANIMATION_CAPTION)
            except Exception:
                pass

            html = (
                f"<p>❍ Hey <a href='tg://user?id={uid}'>{rich_esc(name)}</a>, this is "
                f"<b>{rich_esc(config.BOT_NAME)}</b></p>"
                + rich_note(
                    f"Thanks for adding me in {rich_esc(chat_title)}. "
                    f"{rich_esc(name)} can now play songs here."
                )
                + "<p>"
                + rich_button("⛩️ Add me baby", url=f"{config.BOT_LINK}?startgroup=true", style="success")
                + " "
                + rich_button("🍬 Support", url=config.SUPPORT_GROUP)
                + "<br/>"
                + rich_button("📖 Help & Commands", callback_data="show_help", style="primary")
                + "</p>"
            )
            sent = await rich_reply(message, html, quote=False)
        else:
            classic_caption = (
                f"❍ ʜᴇʏ <a href='tg://user?id={uid}'>{name}</a>,\n"
                f"ᴛʜɪs ɪs <b>{config.BOT_NAME}</b>\n\n"
                f"ᴛʜᴀɴᴋs ғᴏʀ ᴀᴅᴅɪɴɢ ᴍᴇ ɪɴ <b>{chat_title}</b>.\n"
                f"{name} ᴄᴀɴ ɴᴏᴡ ᴘʟᴀʏ sᴏɴɢs ʜᴇʀᴇ."
            )
            classic_kb = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⛩️ ᴧᴅᴅ мᴇ ʙᴧʙʏ ⛩️",
                                         url=f"{config.BOT_LINK}?startgroup=true"),
                    InlineKeyboardButton("🍬 sᴜᴘᴘᴏʀᴛ 🍬", url=config.SUPPORT_GROUP),
                ],
                [InlineKeyboardButton("🏩 ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs 🏩",
                                      callback_data="show_help")],
            ])
            sent = await message.reply_animation(
                animation,
                caption=classic_caption,
                parse_mode=ParseMode.HTML,
                reply_markup=classic_kb,
            )

        if config.LOGGER_ID and RICH_AVAILABLE:
            try:
                await rich_send(bot, config.LOGGER_ID, _new_group_log_html(message.chat, name))
            except Exception:
                pass

        admin_msg = (
            "<b>╭──────────────────────▣</b>\n"
            "<b>│❍ ᴛʜᴀɴᴋs ғᴏʀ ᴀᴅᴅɪɴɢ ᴍᴇ! 🥀</b>\n"
            "<b>├──────────────────────▣</b>\n"
            "<b>│❍ ᴘʟᴇᴀsᴇ ᴍᴀᴋᴇ ᴍᴇ ᴀɴ ᴀᴅᴍɪɴ</b>\n"
            "<b>│  ᴡɪᴛʜ ᴛʜᴇsᴇ ᴘᴇʀᴍɪssɪᴏɴs:</b>\n"
            "<b>├──────────────────────▣</b>\n"
            "<b>│ ❍ ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇs</b>\n"
            "<b>│ ❍ ᴍᴀɴᴀɢᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛs</b>\n"
            "<b>│ ❍ ɪɴᴠɪᴛᴇ ᴜsᴇʀs</b>\n"
            "<b>├──────────────────────▣</b>\n"
            "<b>│❍ ᴡɪᴛʜᴏᴜᴛ ᴀᴅᴍɪɴ ᴘᴇʀᴍs</b>\n"
            "<b>│  sᴏᴍᴇ ғᴇᴀᴛᴜʀᴇs ᴡᴏɴ'ᴛ ᴡᴏʀᴋ! 🚫</b>\n"
            "<b>╰──────────────────────▣</b>"
        )
        admin_kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "⚡ ᴍᴀᴋᴇ ᴍᴇ ᴀᴅᴍɪɴ ⚡",
                url=f"tg://user?id={(await bot.get_me()).id}",
            )
        ]])
        try:
            admin_sent = await message.reply_text(
                admin_msg,
                parse_mode=ParseMode.HTML,
                reply_markup=admin_kb,
            )
        except Exception:
            pass

        try:
            add_broadcast_chat(chat_id, "group")
        except Exception:
            pass


# ── /help ─────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("help") & user_allowed)
async def help_handler(_, message: Message) -> None:

    uid  = message.from_user.id
    name = message.from_user.first_name or "User"

    # ── Delete the user's /help command message ───────────────────────────────
    try:
        await message.delete()
    except Exception:
        pass

    animation = random.choice(START_ANIMATIONS)

    if RICH_AVAILABLE:
        try:
            await message.reply_animation(animation, caption=_ANIMATION_CAPTION)
        except Exception:
            pass
        sent = await rich_reply(message, _help_entry_html(), quote=False)
    else:
        classic_caption, classic_kb = _classic_help_entry(uid, name)
        sent = await message.reply_animation(
            animation,
            caption=classic_caption,
            parse_mode=ParseMode.HTML,
            reply_markup=classic_kb,
)

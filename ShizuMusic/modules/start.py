# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------
#--------------------------------------------

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
    rich_note,
    rich_reply,
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


def _rich_start_private_html(uid, name):
    button_row1 = " ".join([
        rich_button("⛩️ Add me baby", url=f"{config.BOT_LINK}?startgroup=true", style="success"),
    ])
    button_row2 = " ".join([
        rich_button("🍬 Support", url=config.SUPPORT_GROUP),
        rich_button("🍹 Updates", url=config.UPDATES_CHANNEL),
    ])
    button_row3 = rich_button("🏩 Help & Commands", callback_data="show_help", style="primary")
    button_row4 = " ".join([
        rich_button("🫧 Owner", url=f"tg://user?id={config.OWNER_ID}"),
        rich_button("🍡 Source", url="https://github.com/Badmunda05/ShizuMusic/fork"),
    ])

    return (
        rich_heading(f"Hey {rich_esc(name)} 🥀", level=3)
        + f"<p>This is <b>{rich_esc(config.BOT_NAME)}</b> — a fast &amp; powerful "
          "Telegram music player bot.</p>"
        + rich_details(
            "What can I do?",
            "<p>Play music in group voice chats from YouTube, Spotify, and "
            "more. Tap Help below for the full command list.</p>",
            open=True,
        )
        + rich_note(f"Powered by <a href='https://t.me/PBXCHATS'>sʜɪᴢᴜ-ᴍᴜsɪᴄ™</a>")
        + f"<p>{button_row1}<br/>{button_row2}<br/>{button_row3}<br/>{button_row4}</p>"
    )


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
            # Animation for visual flair — captions can't carry rich tags,
            # so keep it short and let the follow-up rich message do the work.
            try:
                await message.reply_animation(
                    animation,
                    caption=_ANIMATION_CAPTION,
                    message_effect_id=random.choice(EFFECT_ID),
                )
            except Exception:
                pass

            sent = await rich_reply(
                message,
                _rich_start_private_html(uid, name),
                quote=False,
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
                + rich_button("🏩 Help & Commands", callback_data="show_help", style="primary")
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

        rows = [
            [("Admin", "help_admin"), ("A-Play", "help_autoplay"), ("G-Cast", "help_gcast")],
            [("Bl-Chat", "help_blchat"), ("Bl-Users", "help_blusers"), ("Ping", "help_ping")],
            [("Play", "help_play"), ("Speed", "help_speed"), ("Info", "help_info")],
        ]
        button_html = "".join(
            "<p>" + " ".join(rich_button(text, callback_data=cb) for text, cb in row) + "</p>"
            for row in rows
        )
        button_html += f"<p>{rich_button('⌯ Close ⌯', callback_data='close_help', style='danger')}</p>"

        html = (
            rich_heading(f"Hey {rich_esc(name)} 🥀", level=3)
            + "<p>📜 Choose a category:</p>"
            + button_html
            + rich_note(f"Powered by <a href='https://t.me/PBXCHATS'>sʜɪᴢᴜ-ᴍᴜsɪᴄ™</a>")
        )
        sent = await rich_reply(message, html, quote=False)
        return

    classic_kb = InlineKeyboardMarkup([
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
        [
            InlineKeyboardButton("⌯ ᴄʟᴏsᴇ ⌯", callback_data="close_help"),
        ],
    ])
    sent = await message.reply_animation(
        animation,
        caption=(
            "<b>╭────────────────────▣</b>\n"
            f"<b>│❍ ʜᴇʏ</b> <a href='tg://user?id={uid}'>{name}</a>, 🥀\n"
            "<b>├────────────────────▣</b>\n"
            "<b>│📜 ᴄʜᴏᴏsᴇ ᴀ ᴄᴀᴛᴇɢᴏʀʏ :</b>\n"
            "<b>├────────────────────▣</b>\n"
            f"<b>│❍ ᴘᴏᴡᴇʀᴇᴅ ʙʏ » "
            f"<a href='https://t.me/PBXCHATS'>sʜɪᴢᴜ-ᴍᴜsɪᴄ™</a></b>\n"
            "<b>╰────────────────────▣</b>"
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=classic_kb,
    )

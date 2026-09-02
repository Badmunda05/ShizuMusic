# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------
#
#  Text content is ShizuMusic's own (same features as the old ASCII-box
#  version) — only the STRUCTURE changed, matching the reference bot's
#  pattern: heading, a collapsible "Key Features" table, a "Why choose"
#  list, all via rich_ui's block helpers so it actually renders as
#  headings/tables/collapsible sections instead of plain lines.
# --------------------------------------------------------------------------------

import random

from pyrogram import enums, filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from ShizuMusic import bot
from config import START_ANIMATIONS
from ShizuMusic.modules.block import user_allowed
from ShizuMusic.utils.db import add_broadcast_chat, add_served_chat, add_served_user
from ShizuMusic.utils.rich_ui import (
    rich_details,
    rich_esc,
    rich_heading,
    rich_note,
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


def _support_updates_pills() -> str:
    return (
        "<p>"
        f'<tg-button type="url" style="primary" url="{config.SUPPORT_GROUP}">'
        "🍬 Support</tg-button> "
        f'<tg-button type="url" style="success" url="{config.UPDATES_CHANNEL}">'
        "🍹 Updates</tg-button>"
        "</p>"
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

        # Animation on its own — captions can't be rich.
        try:
            await message.reply_animation(
                animation,
            )
        except Exception:
            pass

        caption = (
            f"<p>❍ Hey <a href='tg://user?id={uid}'>{rich_esc(name)}</a>, "
            "welcome aboard! 🎶</p>"
            + f"<p>I am <b>{rich_esc(config.BOT_NAME)}</b> — a fast &amp; "
              "powerful Telegram music player bot with some awesome "
              "features.</p>"
            + rich_details(
                "✦ Key Features ✦",
                rich_table(
                    ["Feature", "Details"],
                    [
                        ("🎵 Streaming", "Play audio &amp; video in voice chats"),
                        ("🔁 Autoplay", "Keeps the queue going automatically"),
                        ("🎚️ Effects", "Speed control &amp; bass boost"),
                        ("🛡️ Moderation", "Block/unblock chats &amp; users"),
                    ],
                ),
                open=True,
            )
            + rich_details(
                "✧ Why choose it? ✧",
                "<p>⭐ Simple slash commands, no setup needed.</p>"
                "<p>🎧 Clean, low-lag streaming.</p>"
                "<p>❍ Click Help below for all commands.</p>",
                open=True,
            )
            + rich_note(f"Powered by » <a href='https://t.me/PBXCHATS'>sʜɪᴢᴜ-ᴍᴜsɪᴄ™</a>")
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

        sent = await rich_send(bot, chat_id, caption, reply_markup=kb)

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
        chat_title = message.chat.title or "this chat"

        try:
            await message.reply_animation(animation)
        except Exception:
            pass

        caption = (
            f"<p>❍ Hey <a href='tg://user?id={uid}'>{rich_esc(name)}</a>, "
            f"this is <b>{rich_esc(config.BOT_NAME)}</b></p>"
            + rich_note(
                f"Thanks for adding me in {rich_esc(chat_title)}. "
                f"{rich_esc(name)} can now play songs here."
            )
            + _support_updates_pills()
        )
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⛩️ ᴧᴅᴅ мᴇ ʙᴧʙʏ ⛩️",
                                     url=f"{config.BOT_LINK}?startgroup=true",
                                     style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton("🍬 sᴜᴘᴘᴏʀᴛ 🍬", url=config.SUPPORT_GROUP,
                                     style=enums.ButtonStyle.SUCCESS),
            ],
            [InlineKeyboardButton("🏩 ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs 🏩",
                                  callback_data="show_help",
                                  style=enums.ButtonStyle.PRIMARY)],
        ])

        sent = await rich_send(bot, chat_id, caption, reply_markup=kb)

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
                style=enums.ButtonStyle.DANGER,
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

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ᴧᴅᴍɪɴ",    callback_data="help_admin", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("ᴧ-ᴘʟᴀʏ",   callback_data="help_autoplay", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("ɢ-ᴄᴧsᴛ",   callback_data="help_gcast", style=enums.ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton("ʙʟ-ᴄʜᴧᴛ",  callback_data="help_blchat", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("ʙʟ-ᴜsᴇʀs", callback_data="help_blusers", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("ᴘɪɴɢ",     callback_data="help_ping", style=enums.ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton("ᴘʟᴀʏ",     callback_data="help_play", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("sᴘᴇᴇᴅ",    callback_data="help_speed", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("ɪɴғᴏ",     callback_data="help_info", style=enums.ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton("⌯ ᴄʟᴏsᴇ ⌯", callback_data="close_help", style=enums.ButtonStyle.DANGER),
        ],
    ])

    animation = random.choice(START_ANIMATIONS)

    try:
        await message.reply_animation(animation)
    except Exception:
        pass

    caption = (
        f"{rich_heading('📜 Choose a category', level=3)}"
        f"<p>❍ Hey <a href='tg://user?id={uid}'>{rich_esc(name)}</a>, pick a "
        "category below to see its commands.</p>"
        + rich_note(f"Powered by » <a href='https://t.me/PBXCHATS'>sʜɪᴢᴜ-ᴍᴜsɪᴄ™</a>")
    )

    await rich_send(bot, message.chat.id, caption, reply_markup=kb)

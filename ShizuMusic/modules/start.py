# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio
import random

from pyrogram import enums, filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from ShizuMusic import bot
from config import START_PHOTOS
from ShizuMusic.modules.block import user_allowed
from ShizuMusic.utils.db import add_broadcast_chat, add_served_chat, add_served_user
from ShizuMusic.utils.rich_ui import (
    rich_details,
    rich_esc,
    rich_heading,
    rich_img,
    rich_note,
    rich_send,
    rich_table,
    sanitize_display_name,
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
        "🍬 sᴜᴘᴘᴏʀᴛ</tg-button> "
        f'<tg-button type="url" style="success" url="{config.UPDATES_CHANNEL}">'
        "🍹 ᴜᴘᴅᴀᴛᴇs</tg-button>"
        "</p>"
    )


# ── /start ─────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("start") & user_allowed)
async def start_handler(_, message: Message) -> None:

    uid       = message.from_user.id
    name      = sanitize_display_name(message.from_user.first_name)
    chat_id   = message.chat.id
    chat_type = message.chat.type
    photo     = random.choice(config.START_PHOTOS)

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

        caption = (
            rich_img(photo)
            + f"<p>❍ ʜᴇʏ <a href='tg://user?id={uid}'>{rich_esc(name)}</a>, "
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

        try:
            sent = await rich_send(bot, chat_id, caption, reply_markup=kb)
        except FloodWait as fw:
            await asyncio.sleep(fw.value + 1)
            sent = await rich_send(bot, chat_id, caption, reply_markup=kb)

        try:
            add_broadcast_chat(chat_id, "private")
        except Exception:
            pass

        if config.LOGGER_ID:
            try:
                logger_caption = (
                    rich_heading("#ɴᴇᴡᴜsᴇʀ sᴛᴀʀᴛᴇᴅ", level=2)
                    + "<p>"
                    + f"<b>❍ ɴᴀᴍᴇ     :</b> <a href='tg://user?id={uid}'>{rich_esc(name)}</a><br>"
                    + f"<b>❍ ɪᴅ       :</b> <code>{uid}</code><br>"
                    + f"<b>❍ ᴜsᴇʀɴᴀᴍᴇ :</b> @{rich_esc(message.from_user.username) or 'N/A'}"
                    + "</p>"
                )
                await rich_send(bot, config.LOGGER_ID, logger_caption)
            except Exception:
                pass

    # ── Group ────────────────────────────────────────────────────────────────
    else:
        chat_title = message.chat.title or "this chat"

        caption = (
            rich_img(photo)
            + f"<p>❍ ʜᴇʏ <a href='tg://user?id={uid}'>{rich_esc(name)}</a>, "
            f"ᴛʜɪs ɪs <b>{rich_esc(config.BOT_NAME)}</b></p>"
            + rich_note(
                f"ᴛʜᴀɴᴋs ғᴏʀ ᴀᴅᴅɪɴɢ ᴍᴇ ɪɴ {rich_esc(chat_title)}. "
                f"{rich_esc(name)} ᴄᴀɴ ɴᴏᴡ ᴘʟᴀʏ sᴏɴɢs ʜᴇʀᴇ."
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

        try:
            sent = await rich_send(bot, chat_id, caption, reply_markup=kb)
        except FloodWait as fw:
            await asyncio.sleep(fw.value + 1)
            sent = await rich_send(bot, chat_id, caption, reply_markup=kb)

        admin_msg = (
            rich_heading("ᴛʜᴀɴᴋs ғᴏʀ ᴀᴅᴅɪɴɢ ᴍᴇ! 🥀", level=2)
            + rich_note(
                "<p>ᴘʟᴇᴀsᴇ ᴍᴀᴋᴇ ᴍᴇ ᴀɴ ᴀᴅᴍɪɴ ᴡɪᴛʜ ᴛʜᴇsᴇ ᴘᴇʀᴍɪssɪᴏɴs:</p>"
                "<p>❍ ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇs<br>"
                "❍ ᴍᴀɴᴀɢᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛs<br>"
                "❍ ɪɴᴠɪᴛᴇ ᴜsᴇʀs</p>"
            )
            + rich_note("ᴡɪᴛʜᴏᴜᴛ ᴀᴅᴍɪɴ ᴘᴇʀᴍs sᴏᴍᴇ ғᴇᴀᴛᴜʀᴇs ᴡᴏɴ'ᴛ ᴡᴏʀᴋ! 🚫")
        )
        admin_kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "⚡ ᴍᴀᴋᴇ ᴍᴇ ᴀᴅᴍɪɴ ⚡",
                url=f"tg://user?id={(await bot.get_me()).id}",
                style=enums.ButtonStyle.DANGER,
            )
        ]])
        try:
            admin_sent = await rich_send(
                bot, chat_id,
                admin_msg,
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
    name = sanitize_display_name(message.from_user.first_name)

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

    photo = random.choice(config.START_PHOTOS)

    caption = (
        rich_img(photo)
        + rich_heading('📜 ᴄʜᴏᴏsᴇ ᴀ ᴄᴀᴛᴇɢᴏʀʏ', level=3)
        + f"<p>❍ ʜᴇʏ <a href='tg://user?id={uid}'>{rich_esc(name)}</a>, ᴘɪᴄᴋ ᴀ "
        "ᴄᴀᴛᴇɢᴏʀʏ ʙᴇʟᴏᴡ ᴛᴏ sᴇᴇ ɪᴛs ᴄᴏᴍᴍᴀɴᴅs.</p>"
        + rich_note(f"ᴘᴏᴡᴇʀᴇᴅ ʙʏ » <a href='https://t.me/PBXCHATS'>sʜɪᴢᴜ-ᴍᴜsɪᴄ™</a>")
    )

    await rich_send(bot, message.chat.id, caption, reply_markup=kb)
    

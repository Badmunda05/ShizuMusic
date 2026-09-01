# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------
#
#  NOTE ON THE NEW "RICH MESSAGE" TAGS (aside / details / tg-button / tg-map /
#  tg-collage / tg-slideshow / tg-time) — Bot API 10.3, Aug 2026:
#
#  - <u>, <ins>, <sub>, <sup>, and <tg-emoji> are classic HTML formatting
#    entities that already work today with plain parse_mode=HTML. Those are
#    used directly below with full confidence.
#
#  - <aside>, <details>/<summary>, <tg-map>, <tg-collage>, <tg-slideshow>,
#    <tg-button>, <tg-time> belong to the new *rich message* content type
#    (same family as the Go `InputRichMessage` you showed me) — NOT plain
#    text formatting. Whether pyrofork==2.3.69 (pinned in requirements.txt)
#    already exposes a send method for this is something I can't verify —
#    it's past my training cutoff and I don't have search here. So this
#    file:
#       1. Builds the new-style rich HTML as rich_html string constants.
#       2. Tries to send it via `bot.send_rich_message` IF that attribute
#          exists on your installed pyrofork Client (hasattr guard below —
#          this is a guess at the method name, check pyrofork's actual
#          changelog/`dir(bot)` and fix the call if the real name differs).
#       3. Falls back to the original, guaranteed-working
#          reply_animation + InlineKeyboardMarkup flow if step 2 isn't
#          available or throws.
#
#  Set config.USE_RICH_MESSAGES = True once you've confirmed step 2 actually
#  works on your pyrofork build — until then this safely no-ops to classic.
# --------------------------------------------------------------------------------

import asyncio
import random

from pyrogram import filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from ShizuMusic import bot
from config import START_ANIMATIONS
from ShizuMusic.modules.block import user_allowed
from ShizuMusic.utils.db import add_broadcast_chat, add_served_chat, add_served_user

RICH_MODE = getattr(config, "USE_RICH_MESSAGES", False)

# ── Message effect IDs (Telegram premium effects) ─────────────────────────────
EFFECT_ID = [
    5046509860389126442,
    5107584321108051014,
    5104841245755180586,
    5159385139981059251,
]


async def send_adaptive(message: Message, *, rich_html: str, animation, classic_caption: str,
                         classic_kb: InlineKeyboardMarkup, effect_id=None):
    """
    Try the new rich-message send path first (if enabled + available on this
    pyrofork build), otherwise fall back to the classic animation+caption+
    InlineKeyboardMarkup flow that is known to work today.
    """
    if RICH_MODE and hasattr(bot, "send_rich_message"):
        try:
            kwargs = {}
            if effect_id:
                kwargs["message_effect_id"] = effect_id
            return await bot.send_rich_message(
                chat_id=message.chat.id,
                html=rich_html,
                **kwargs,
            )
        except Exception as e:
            print(f"[rich-message] send failed, falling back to classic: {e}")

    kwargs = dict(caption=classic_caption, parse_mode=ParseMode.HTML, reply_markup=classic_kb)
    if effect_id:
        kwargs["message_effect_id"] = effect_id
    return await message.reply_animation(animation, **kwargs)


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

        # Classic caption (guaranteed to render) — kept exactly as before,
        # just with <u> added (already-supported tag) on the tagline.
        classic_caption = (
            "<b>╭────────────────────▣</b>\n"
            f"<b>│❍ ʜᴇʏ</b> <a href='tg://user?id={uid}'>{name}</a>, 🥀\n"
            f"<b>│❍ ᴛʜɪs ɪs <u>{config.BOT_NAME}</u> !</b>\n"
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
        classic_kb = InlineKeyboardMarkup([
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

        # Experimental rich-message version — pull-quote greeting via <aside>,
        # collapsible feature list via <details>, buttons embedded inline via
        # <tg-button> instead of a separate InlineKeyboardMarkup. Only sent if
        # RICH_MODE + bot.send_rich_message actually exist (see send_adaptive).
        rich_html = (
            f"<h3>Hey {name} 🥀</h3>\n"
            f"<p>This is <b><u>{config.BOT_NAME}</u></b>!</p>\n"
            "<aside>A fast &amp; powerful Telegram music player bot with "
            "some awesome features.<cite>sʜɪᴢᴜ-ᴍᴜsɪᴄ™</cite></aside>\n"
            "<details open><summary>What can I do?</summary>"
            "<p>Play music in group voice chats from YouTube, Spotify, and "
            "more &mdash; tap Help below for the full command list.</p>"
            "</details>\n"
            "<p>"
            f"<tg-button type=\"url\" style=\"success\" "
            f"url=\"{config.BOT_LINK}?startgroup=true\">⛩️ Add me baby</tg-button> "
            f"<tg-button type=\"url\" url=\"{config.SUPPORT_GROUP}\">🍬 Support</tg-button> "
            f"<tg-button type=\"url\" url=\"{config.UPDATES_CHANNEL}\">🍹 Updates</tg-button><br/>"
            "<tg-button type=\"callback_data\" style=\"primary\" data=\"show_help\">"
            "🏩 Help &amp; Commands</tg-button><br/>"
            f"<tg-button type=\"url\" url=\"tg://user?id={config.OWNER_ID}\">🫧 Owner</tg-button> "
            "<tg-button type=\"url\" url=\"https://github.com/Badmunda05/ShizuMusic/fork\">"
            "🍡 Source</tg-button>"
            "</p>\n"
            f"<p>Powered by <a href='https://t.me/PBXCHATS'>sʜɪᴢᴜ-ᴍᴜsɪᴄ™</a></p>"
        )

        sent = await send_adaptive(
            message,
            rich_html=rich_html,
            animation=animation,
            classic_caption=classic_caption,
            classic_kb=classic_kb,
            effect_id=random.choice(EFFECT_ID),
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

        classic_caption = (
            f"❍ ʜᴇʏ <a href='tg://user?id={uid}'>{name}</a>,\n"
            f"ᴛʜɪs ɪs <b><u>{config.BOT_NAME}</u></b>\n\n"
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

        rich_html = (
            f"<p>❍ Hey <a href='tg://user?id={uid}'>{name}</a>, this is "
            f"<b><u>{config.BOT_NAME}</u></b></p>\n"
            f"<aside>Thanks for adding me in {chat_title}. {name} can now "
            "play songs here.<cite>sʜɪᴢᴜ-ᴍᴜsɪᴄ™</cite></aside>\n"
            "<p>"
            f"<tg-button type=\"url\" style=\"success\" "
            f"url=\"{config.BOT_LINK}?startgroup=true\">⛩️ Add me baby</tg-button> "
            f"<tg-button type=\"url\" url=\"{config.SUPPORT_GROUP}\">🍬 Support</tg-button><br/>"
            "<tg-button type=\"callback_data\" style=\"primary\" data=\"show_help\">"
            "🏩 Help &amp; Commands</tg-button>"
            "</p>"
        )

        sent = await send_adaptive(
            message,
            rich_html=rich_html,
            animation=animation,
            classic_caption=classic_caption,
            classic_kb=classic_kb,
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

    animation = random.choice(START_ANIMATIONS)

    classic_caption = (
        "<b>╭────────────────────▣</b>\n"
        f"<b>│❍ ʜᴇʏ</b> <a href='tg://user?id={uid}'>{name}</a>, 🥀\n"
        "<b>├────────────────────▣</b>\n"
        "<b>│📜 ᴄʜᴏᴏsᴇ ᴀ ᴄᴀᴛᴇɢᴏʀʏ :</b>\n"
        "<b>├────────────────────▣</b>\n"
        f"<b>│❍ ᴘᴏᴡᴇʀᴇᴅ ʙʏ » "
        f"<a href='https://t.me/PBXCHATS'>sʜɪᴢᴜ-ᴍᴜsɪᴄ™</a></b>\n"
        "<b>╰────────────────────▣</b>"
    )

    # Category buttons grouped in rows via <tg-button>, each category still
    # maps to the same help_* callback_data your callbacks.py already handles.
    rich_html = (
        f"<h3>Hey {name} 🥀</h3>\n"
        "<p>📜 Choose a category:</p>\n"
        "<p>"
        "<tg-button type=\"callback_data\" data=\"help_admin\">Admin</tg-button> "
        "<tg-button type=\"callback_data\" data=\"help_autoplay\">Autoplay</tg-button> "
        "<tg-button type=\"callback_data\" data=\"help_gcast\">Gcast</tg-button><br/>"
        "<tg-button type=\"callback_data\" data=\"help_blchat\">Bl-Chat</tg-button> "
        "<tg-button type=\"callback_data\" data=\"help_blusers\">Bl-Users</tg-button> "
        "<tg-button type=\"callback_data\" data=\"help_ping\">Ping</tg-button><br/>"
        "<tg-button type=\"callback_data\" data=\"help_play\">Play</tg-button> "
        "<tg-button type=\"callback_data\" data=\"help_speed\">Speed</tg-button> "
        "<tg-button type=\"callback_data\" data=\"help_info\">Info</tg-button><br/>"
        "<tg-button type=\"callback_data\" style=\"danger\" data=\"close_help\">"
        "⌯ Close ⌯</tg-button>"
        "</p>\n"
        f"<p>Powered by <a href='https://t.me/PBXCHATS'>sʜɪᴢᴜ-ᴍᴜsɪᴄ™</a></p>"
    )

    sent = await send_adaptive(
        message,
        rich_html=rich_html,
        animation=animation,
        classic_caption=classic_caption,
        classic_kb=classic_kb,
    )

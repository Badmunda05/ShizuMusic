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

from pyrogram import filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.errors import FloodWait
from pyrogram.types import Message

import config
from ShizuMusic import bot
from config import START_PHOTOS
from ShizuMusic.modules.block import user_allowed
from ShizuMusic.strings import DEFAULT_LANG, get_string
from ShizuMusic.utils.buttons import (
    help_menu_kb,
    make_admin_kb,
    start_group_kb,
    start_private_kb,
    support_updates_pills,
)
from ShizuMusic.utils.db import add_broadcast_chat, add_served_chat, add_served_user
from ShizuMusic.utils.language import chat_strings
from ShizuMusic.utils.logs import logger_active
from richgram import (
    rich_details,
    rich_esc,
    rich_heading,
    rich_img,
    rich_kv_table,
    rich_note,
    rich_send,
    rich_table,
    sanitize_display_name,
)

def _onboarding_body(lang: dict, uid: int, name: str) -> str:
    """Shared by /start (private) and the help panel's 'go back' button."""
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


# ── /start ─────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("start") & user_allowed)
async def start_handler(_, message: Message) -> None:

    uid       = message.from_user.id
    name      = sanitize_display_name(message.from_user.first_name)
    chat_id   = message.chat.id
    chat_type = message.chat.type
    photo     = random.choice(config.START_PHOTOS)
    lang      = chat_strings(chat_id)

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

        caption = rich_img(photo) + _onboarding_body(lang, uid, name)
        kb = start_private_kb(lang)

        try:
            sent = await rich_send(bot, chat_id, caption + kb)
        except FloodWait as fw:
            await asyncio.sleep(fw.value + 1)
            sent = await rich_send(bot, chat_id, caption + kb)

        try:
            add_broadcast_chat(chat_id, "private")
        except Exception:
            pass

        # ── Log new user to LOGGER_ID ────────────────────────────────────────
        if logger_active():
            try:
                username = message.from_user.username
                username_display = f"@{rich_esc(username)}" if username else "N/A"

                en = get_string(DEFAULT_LANG)   # log channel is the owner's: always English
                logger_caption = (
                    rich_heading(en["logger_newuser_title"], level=2)
                    + rich_kv_table([
                        (en["kv_name"], f'<a href="tg://user?id={uid}">{rich_esc(name)}</a>'),
                        (en["kv_id"], f"<code>{uid}</code>"),
                        (en["kv_username"], username_display),
                    ])
                )
                await rich_send(bot, config.LOGGER_ID, logger_caption)
            except Exception as e:
                print(f"[start_handler] Failed to send LOGGER_ID message: {e}")

    # ── Group ────────────────────────────────────────────────────────────────
    else:
        chat_title = message.chat.title or "this chat"
        mention = f'<a href="tg://user?id={uid}">{rich_esc(name)}</a>'

        caption = (
            rich_img(photo)
            + f"<p>{lang['group_thanks_title'].format(mention, rich_esc(config.BOT_NAME))}</p>"
            + rich_note(lang["group_thanks_note"].format(rich_esc(chat_title), rich_esc(name)))
            + support_updates_pills(lang)
        )
        kb = start_group_kb(lang)

        try:
            sent = await rich_send(bot, chat_id, caption + kb)
        except FloodWait as fw:
            await asyncio.sleep(fw.value + 1)
            sent = await rich_send(bot, chat_id, caption + kb)

        admin_msg = (
            rich_heading(lang["group_admin_request_title"], level=2)
            + rich_note(lang["group_admin_request_note1"])
            + rich_note(lang["group_admin_request_note2"])
        )
        admin_kb = make_admin_kb((await bot.get_me()).id, styled=True, lang=lang)
        try:
            admin_sent = await rich_send(
                bot, chat_id,
                admin_msg + admin_kb,
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
    lang = chat_strings(message.chat.id)

    # ── Delete the user's /help command message ───────────────────────────────
    try:
        await message.delete()
    except Exception:
        pass

    kb = help_menu_kb(lang)

    photo = random.choice(config.START_PHOTOS)

    caption = (
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

    await rich_send(bot, message.chat.id, caption + kb)
    

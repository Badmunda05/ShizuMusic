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

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import CallbackQuery, Message

from ShizuMusic import bot
from ShizuMusic.modules.block import group_allowed, user_allowed
from ShizuMusic.strings import languages_present
from ShizuMusic.utils.buttons import language_kb
from ShizuMusic.utils.db import get_chat_lang, set_chat_lang
from ShizuMusic.utils.language import chat_strings
from ShizuMusic.utils.permissions import is_user_authorized
from richgram import rich_edit, rich_heading, rich_note, rich_send


def _menu(chat_id: int, is_private: bool, lang: dict, current: str):
    """Rich message (text + buttons) for the language picker in the given language."""
    text = rich_heading(lang["lang_title"], level=3) + rich_note(lang["lang_1"])
    kb = language_kb(languages_present, current, lang=lang, show_home=is_private)
    return text + kb


# ── /language  (groups AND the bot's PM) ───────────────────────────────────────

@bot.on_message(
    filters.command(["language", "setlang", "lang"])
    & group_allowed
    & user_allowed
)
async def language_cmd(_, message: Message) -> None:
    chat_id = message.chat.id
    is_private = message.chat.type == ChatType.PRIVATE
    lang = chat_strings(chat_id)

    text = _menu(chat_id, is_private, lang, get_chat_lang(chat_id))
    await rich_send(bot, chat_id, text)


# ── 🌐 Language button on the /start panel (PM) ───────────────────────────────

@bot.on_callback_query(filters.regex(r"^show_lang$"))
async def show_lang_cb(_, cbq: CallbackQuery) -> None:
    await cbq.answer()
    chat_id = cbq.message.chat.id
    is_private = cbq.message.chat.type == ChatType.PRIVATE
    lang = chat_strings(chat_id)

    text = _menu(chat_id, is_private, lang, get_chat_lang(chat_id))

    # /start's message can be a photo card — swap it for a fresh message.
    try:
        await cbq.message.delete()
    except Exception:
        pass
    await rich_send(bot, chat_id, text)


# ── language picked ───────────────────────────────────────────────────────────

@bot.on_callback_query(filters.regex(r"^setlang:(.+)$"))
async def language_cb(_, cbq: CallbackQuery) -> None:
    chat_id = cbq.message.chat.id
    is_private = cbq.message.chat.type == ChatType.PRIVATE
    lang = chat_strings(chat_id)

    # In a group only admins may change it; in the bot's PM it's your own chat.
    if not is_private and not await is_user_authorized(cbq):
        await cbq.answer(lang["lang_5"], show_alert=True)
        return

    code = cbq.data.split(":", 1)[1]

    if code not in languages_present:
        await cbq.answer(lang["lang_3"], show_alert=True)
        return

    if code == get_chat_lang(chat_id):
        await cbq.answer(lang["lang_4"], show_alert=True)
        return

    set_chat_lang(chat_id, code)

    if not is_private and cbq.from_user:
        try:
            set_chat_lang(cbq.from_user.id, code)
        except Exception:
            pass

    new_lang = chat_strings(chat_id)   # re-read: everything below is in the NEW language

    await cbq.answer(new_lang["lang_2"], show_alert=True)

    try:
        text = _menu(chat_id, is_private, new_lang, code)
        await rich_edit(cbq.message, text)
    except Exception:
        pass
        

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
from pyrogram.types import Message

import config
from ShizuMusic import bot
from ShizuMusic.utils.db import is_logger_enabled, set_logger_enabled
from ShizuMusic.utils.language import chat_strings
from richgram import (
    rich_esc,
    rich_heading,
    rich_kv_table,
    rich_note,
    rich_send,
)


def _status_table(lang: dict) -> str:
    on = is_logger_enabled()
    return rich_kv_table([
        (lang["autoplay_kv_status"],
         lang["autoplay_status_on"] if on else lang["autoplay_status_off"]),
        (lang["logger_kv_target"],
         f"<code>{rich_esc(config.LOGGER_ID)}</code>" if config.LOGGER_ID
         else lang["logger_not_set"]),
    ])


@bot.on_message(filters.command("logger") & filters.user(config.OWNER_ID))
async def logger_cmd(_, message: Message) -> None:

    chat_id = message.chat.id
    lang = chat_strings(chat_id)
    args = [a.lower() for a in message.command[1:]]

    # /logger  ->  status
    if not args or args[0] in ("status", "info"):
        await rich_send(
            bot, chat_id,
            rich_heading(lang["logger_title"], level=3)
            + _status_table(lang)
            + rich_note(lang["logger_usage_note"]),
        )
        return

    if args[0] in ("on", "enable", "start"):
        set_logger_enabled(True)
        note = lang["logger_enabled_note"]
        if not config.LOGGER_ID:
            note += "\n" + lang["logger_no_id_note"]
        await rich_send(
            bot, chat_id,
            rich_heading(lang["logger_enabled_title"], level=3)
            + _status_table(lang)
            + rich_note(note),
        )
        return

    if args[0] in ("off", "disable", "stop"):
        set_logger_enabled(False)
        await rich_send(
            bot, chat_id,
            rich_heading(lang["logger_disabled_title"], level=3)
            + _status_table(lang)
            + rich_note(lang["logger_disabled_note"]),
        )
        return

    await rich_send(
        bot, chat_id,
        rich_heading(lang["logger_title"], level=3)
        + rich_note(lang["logger_usage_note"]),
    )

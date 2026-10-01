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

from ShizuMusic import bot, call_py
from ShizuMusic.core.channels import target_chat
from ShizuMusic.modules.block import group_allowed, user_allowed
from ShizuMusic.utils.language import chat_strings
from ShizuMusic.utils.permissions import is_user_authorized
from richgram import rich_esc, rich_heading, rich_note, rich_send


@bot.on_message(
    filters.group
    & filters.command(["resume", "cresume"])
    & group_allowed
    & user_allowed
)
async def resume_cmd(_, message: Message) -> None:

    chat_id = await target_chat(message)
    if chat_id is None:
        return
    lang = chat_strings(chat_id)

    if not await is_user_authorized(message):
        await rich_send(
            bot, chat_id,
            rich_heading(lang["admin_only_title"], level=3)
            + rich_note(lang["admin_only_note"]),
        )
        return

    try:
        await call_py.resume(chat_id)
        await rich_send(
            bot, chat_id,
            rich_heading(lang["resume_title"], level=3)
            + rich_note(lang["resume_note"]),
        )
    except Exception as e:
        await rich_send(
            bot, chat_id,
            rich_heading(lang["resume_failed_title"], level=3)
            + rich_note(f"<code>{rich_esc(e)}</code>"),
        )


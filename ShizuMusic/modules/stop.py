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

from ShizuMusic import bot
from ShizuMusic.core.channels import target_chat
from ShizuMusic.core.call import leave_vc
from ShizuMusic.core.queue import clear_queue, queue_size
from ShizuMusic.modules.block import group_allowed, user_allowed
from ShizuMusic.utils.language import chat_strings
from ShizuMusic.utils.permissions import is_user_authorized
from richgram import rich_heading, rich_note, rich_send


# ── /stop & /end ──────────────────────────────────────────────────────────────

@bot.on_message(
    filters.group
    & filters.command(["stop", "end", "cstop", "cend"])
    & group_allowed
    & user_allowed
)
async def stop_cmd(_, message: Message) -> None:

    chat_id = await target_chat(message)
    if chat_id is None:
        return
    lang = chat_strings(chat_id)

    if not await is_user_authorized(message):
        await rich_send(bot, chat_id, rich_heading(lang["admin_only_title"], level=3))
        return

    await leave_vc(chat_id)

    await rich_send(
        bot, chat_id,
        rich_heading(lang["stop_stopped_title"], level=3)
        + rich_note(lang["stop_stopped_note"]),
    )


# ── /clear ─────────────────────────────────────────────────────────────────────

@bot.on_message(
    filters.group
    & filters.command(["clear", "cclear"])
    & group_allowed
    & user_allowed
)
async def clear_cmd(_, message: Message) -> None:

    chat_id = await target_chat(message)
    if chat_id is None:
        return
    lang = chat_strings(chat_id)

    if not await is_user_authorized(message):
        await rich_send(bot, chat_id, rich_heading(lang["admin_only_title"], level=3))
        return

    try:
        from ShizuMusic.core.autoplay import reset_autoplay_state
        reset_autoplay_state(chat_id)
    except Exception:
        pass

    if not queue_size(chat_id):
        await rich_send(bot, chat_id, rich_heading(lang["queue_empty_title"], level=3))
        return

    clear_queue(chat_id)
    await rich_send(
        bot, chat_id,
        rich_heading(lang["clear_cleared_title"], level=3)
        + rich_note(lang["clear_cleared_note"]),
    )


# ── /reboot ────────────────────────────────────────────────────────────────────

@bot.on_message(
    filters.command("reboot")
    & group_allowed
    & user_allowed
)
async def reboot_cmd(_, message: Message) -> None:
    chat_id = message.chat.id
    lang = chat_strings(chat_id)
    await leave_vc(chat_id)
    await rich_send(
        bot, chat_id,
        rich_heading(lang["reboot_title"], level=3)
        + rich_note(lang["reboot_note"]),
    )


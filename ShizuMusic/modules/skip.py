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
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from ShizuMusic import bot
from ShizuMusic.core.channels import target_chat
from ShizuMusic.core.player import play_song
from ShizuMusic.core.queue import peek_current, pop_current, queue_size
from ShizuMusic.modules.block import group_allowed, user_allowed
from ShizuMusic.utils.formatters import short
from ShizuMusic.utils.helpers import delete_file
from ShizuMusic.utils.language import chat_strings
from ShizuMusic.utils.permissions import is_user_authorized
from richgram import (
    rich_edit,
    rich_esc,
    rich_heading,
    rich_kv_table,
    rich_note,
    rich_send,
)


@bot.on_message(
    filters.group
    & filters.command(["skip", "cskip"])
    & group_allowed
    & user_allowed
)
async def skip_cmd(_, message: Message) -> None:

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

    if not queue_size(chat_id):
        await rich_send(
            bot, chat_id,
            rich_heading(lang["queue_empty_title"], level=3)
            + rich_note(lang["skip_empty_note"]),
        )
        return

    sm = await rich_send(bot, chat_id, rich_heading(lang["skip_skipping_title"], level=3))

    skipped = pop_current(chat_id)

    try:
        delete_file(skipped.get("file_path", ""))
    except Exception:
        pass

    nxt = peek_current(chat_id)

    if not nxt:
        # queue is empty: let AutoPlay (if ON) add one related song
        try:
            from ShizuMusic.core.autoplay import autoplay_next
            if await autoplay_next(chat_id, skipped):
                nxt = peek_current(chat_id)
        except Exception:
            pass

    if nxt:
        try:
            from ShizuMusic.core.autoplay import schedule_prefetch
            schedule_prefetch(chat_id, nxt)
        except Exception:
            pass

        await rich_edit(
            sm,
            rich_heading(lang["skip_skipped_title"], level=3)
            + rich_kv_table([
                (lang["kv_skipped"], f"<code>{rich_esc(short(skipped['title']))}</code>"),
                (lang["kv_now_playing"], f"<code>{rich_esc(nxt['title'])}</code>"),
            ]),
        )
        dm = await rich_send(
            bot, chat_id,
            rich_heading(lang["next_track_title"], level=3)
            + rich_kv_table([(lang["kv_title"], f"<code>{rich_esc(nxt['title'])}</code>")]),
        )
        await play_song(chat_id, dm, nxt)
    else:
        await rich_edit(
            sm,
            rich_heading(lang["skip_skipped_title"], level=3)
            + rich_kv_table([(lang["kv_skipped"], f"<code>{rich_esc(short(skipped['title']))}</code>")])
            + rich_note(lang["skip_queue_empty_note"]),
        )


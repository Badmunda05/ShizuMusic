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

import re

from pyrogram import filters
from pyrogram.types import Message

import config
from ShizuMusic import bot
from ShizuMusic.core.channels import target_chat
from ShizuMusic.core.player import play_song
from ShizuMusic.core.queue import push_front
from ShizuMusic.modules.block import group_allowed, user_allowed
from ShizuMusic.modules.play import BLOCKED_WORDS
from ShizuMusic.utils.assistant import is_assistant_in, try_join_assistant
from ShizuMusic.utils.db import add_served_chat, add_served_user
from ShizuMusic.utils.formatters import iso_to_human, iso_to_sec
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
from ShizuMusic.utils.youtube import search_yt


@bot.on_message(
    filters.group
    & filters.command(["playforce", "vplayforce", "cplayforce", "cvplayforce"])
    & group_allowed
    & user_allowed
)
async def playforce_cmd(_, message: Message) -> None:

    chat_id = await target_chat(message)      # group, or the linked channel for /cplayforce
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

    video = "vplayforce" in message.command[0].lower()
    parts = (message.text or "").split(None, 1)
    query = parts[1].strip() if len(parts) > 1 else ""

    try:
        await message.delete()
    except Exception:
        pass

    if not query:
        await rich_send(
            bot, chat_id,
            rich_heading(lang["pf_usage_title"], level=3)
            + rich_note(lang["pf_usage_note"]),
        )
        return

    if any(x in query.lower() for x in BLOCKED_WORDS):
        await rich_send(bot, chat_id, rich_heading(lang["play_blocked_title"], level=3))
        return

    pm = await rich_send(bot, chat_id, rich_heading(lang["play_processing_title"], level=3))

    # ── assistant must be in the group (same flow as /play) ─────────────────────
    status = await is_assistant_in(chat_id)

    if status == "banned":
        await rich_edit(
            pm,
            rich_heading(lang["play_assistant_banned_title"], level=3)
            + rich_note(lang["play_assistant_banned_note"]),
        )
        return

    if not status:
        await rich_edit(pm, rich_heading(lang["play_assistant_joining_title"], level=3))
        if not await try_join_assistant(chat_id, pm):
            return

    if "youtu.be" in query:
        m = re.search(r"youtu\.be/([^?&]+)", query)
        if m:
            query = f"https://www.youtube.com/watch?v={m.group(1)}"

    try:
        result = await search_yt(query)
    except Exception as e:
        await rich_edit(
            pm,
            rich_heading(lang["play_search_failed_title"], level=3)
            + rich_note(f"<code>{rich_esc(e)}</code>"),
        )
        return

    # A playlist link: force-play only its first song.
    if isinstance(result, dict) and "playlist" in result:
        items = result["playlist"]
        if not items:
            await rich_edit(pm, rich_heading(lang["play_playlist_empty_title"], level=3))
            return
        it = items[0]
        url, title, dur_iso, thumb = it["link"], it["title"], it["duration"], it["thumbnail"]
    else:
        url, title, dur_iso, thumb = result

    if not url:
        await rich_edit(pm, rich_heading(lang["play_song_not_found_title"], level=3))
        return

    secs = iso_to_sec(dur_iso)
    if secs > config.MAX_DURATION_SECONDS:
        await rich_edit(
            pm,
            rich_heading(lang["play_song_too_long_title"], level=3)
            + rich_kv_table([
                (lang["kv_dur"], f"<code>{iso_to_human(dur_iso)}</code>"),
                (lang["kv_max"], f"<code>{config.MAX_DURATION_SECONDS // 60} min</code>"),
            ]),
        )
        return

    user = message.from_user
    song = {
        "url":              url,
        "title":            title,
        "duration":         iso_to_human(dur_iso),
        "duration_seconds": secs,
        "requester":        user.first_name if user else "Unknown",
        "requester_id":     user.id if user else 0,
        "thumbnail":        thumb,
        "video":            video,
    }

    try:
        add_served_chat(message.chat.id)
        if user:
            add_served_user(user.id)
    except Exception:
        pass

    # Forced song takes slot 0; the old song + rest of the queue stay behind it.
    push_front(chat_id, song)
    await play_song(chat_id, pm, song)

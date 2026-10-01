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

import math
import re

from pyrogram import filters
from pyrogram.types import Message

import config
from ShizuMusic import bot
from ShizuMusic.core.channels import target_chat
from ShizuMusic.core.player import play_song
from ShizuMusic.core.queue import add_to_queue, peek_current, queue_size
from ShizuMusic.modules.block import group_allowed, user_allowed
from ShizuMusic.modules.play import BLOCKED_WORDS
from ShizuMusic.utils.assistant import is_assistant_in, try_join_assistant
from ShizuMusic.utils.db import (
    add_served_chat,
    add_songs_to_playlist,
    create_playlist,
    delete_playlist,
    get_playlist,
    get_user_playlists,
    playlist_db_ready,
    remove_song_from_playlist,
)
from ShizuMusic.utils.formatters import iso_to_human, iso_to_sec, short
from ShizuMusic.utils.language import chat_strings
from richgram import (
    rich_edit,
    rich_esc,
    rich_heading,
    rich_kv_table,
    rich_note,
    rich_send,
    rich_table,
)
from ShizuMusic.utils.youtube import search_yt

_NAME_RE  = re.compile(r"^[\w\-]{1,20}$")
_PAGE_SIZE = 15


# ── helpers ────────────────────────────────────────────────────────────────────

def _parts(message: Message, maxsplit: int) -> list[str]:
    """Words after the command (keeps the tail of the text in one piece)."""
    return (message.text or "").split(None, maxsplit)[1:]


def _code(value) -> str:
    return f"<code>{rich_esc(value)}</code>"


async def _reply(message: Message, title: str, note: str = "", rows=None) -> None:
    body = rich_heading(title, level=3)
    if rows:
        body += rich_kv_table(rows)
    if note:
        body += rich_note(note)
    await rich_send(bot, message.chat.id, body)


async def _db_ok(message: Message, lang: dict) -> bool:
    if playlist_db_ready():
        return True
    await _reply(message, lang["pl_nodb_title"], lang["pl_nodb_note"])
    return False


async def _get_pl(message: Message, lang: dict, name: str):
    """Validate the name and fetch the caller's playlist (replies on failure)."""
    if not _NAME_RE.match(name):
        await _reply(message, lang["pl_bad_name_title"], lang["pl_bad_name_note"])
        return None
    pl = get_playlist(message.from_user.id, name)
    if pl is None:
        await _reply(
            message, lang["pl_not_found_title"],
            lang["pl_not_found_note"].format(rich_esc(name)),
        )
    return pl


def _pack(url: str, title: str, dur_iso: str, thumb: str) -> dict:
    return {
        "url":              url,
        "title":            title,
        "duration":         iso_to_human(dur_iso),
        "duration_seconds": iso_to_sec(dur_iso),
        "thumbnail":        thumb or "",
    }


# ── /pcreate ───────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("pcreate") & group_allowed & user_allowed)
async def pcreate_cmd(_, message: Message) -> None:
    lang = chat_strings(message.chat.id)
    if not message.from_user:
        return

    args = _parts(message, 1)
    if not args:
        await _reply(message, lang["pl_create_usage_title"], lang["pl_create_usage_note"])
        return

    name = args[0].split()[0]
    if not _NAME_RE.match(name):
        await _reply(message, lang["pl_bad_name_title"], lang["pl_bad_name_note"])
        return
    if not await _db_ok(message, lang):
        return

    result = create_playlist(message.from_user.id, name, config.PLAYLIST_LIMIT)

    if result == "ok":
        await _reply(
            message, lang["pl_created_title"],
            lang["pl_created_note"].format(rich_esc(name)),
        )
    elif result == "exists":
        await _reply(message, lang["pl_exists_title"], lang["pl_exists_note"].format(rich_esc(name)))
    elif result == "limit":
        await _reply(message, lang["pl_limit_title"], lang["pl_limit_note"].format(config.PLAYLIST_LIMIT))
    else:
        await _reply(message, lang["pl_nodb_title"], lang["pl_nodb_note"])


# ── /padd ──────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("padd") & group_allowed & user_allowed)
async def padd_cmd(_, message: Message) -> None:
    chat_id = message.chat.id
    lang = chat_strings(chat_id)
    if not message.from_user:
        return

    args  = _parts(message, 2)
    if not args:
        await _reply(message, lang["pl_add_usage_title"], lang["pl_add_usage_note"])
        return

    name  = args[0]
    query = args[1].strip() if len(args) > 1 else ""

    if not await _db_ok(message, lang):
        return
    pl = await _get_pl(message, lang, name)
    if pl is None:
        return
    name = pl["name"]                      # keep the original capitalisation

    user_id = message.from_user.id
    pm      = None
    songs: list[dict] = []
    skipped_long = 0

    # /padd <name>  ->  the song that is playing right now
    if not query:
        cur = peek_current(chat_id)
        if not cur or not str(cur.get("url", "")).startswith("http"):
            await _reply(message, lang["pl_add_usage_title"], lang["pl_add_usage_note"])
            return
        songs = [{
            "url":              cur["url"],
            "title":            cur.get("title", "Unknown"),
            "duration":         cur.get("duration", "?"),
            "duration_seconds": cur.get("duration_seconds", 0),
            "thumbnail":        cur.get("thumbnail", "") or "",
        }]

    else:
        if any(x in query.lower() for x in BLOCKED_WORDS):
            await _reply(message, lang["play_blocked_title"])
            return

        pm = await rich_send(bot, chat_id, rich_heading(lang["pl_searching_title"], level=3))

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

        if isinstance(result, dict) and "playlist" in result:
            for item in result["playlist"]:
                if iso_to_sec(item["duration"]) > config.MAX_DURATION_SECONDS:
                    skipped_long += 1
                    continue
                songs.append(_pack(item["link"], item["title"], item["duration"], item["thumbnail"]))
        else:
            url, title, dur_iso, thumb = result
            if not url:
                await rich_edit(pm, rich_heading(lang["play_song_not_found_title"], level=3))
                return
            if iso_to_sec(dur_iso) > config.MAX_DURATION_SECONDS:
                await rich_edit(
                    pm,
                    rich_heading(lang["play_song_too_long_title"], level=3)
                    + rich_kv_table([
                        (lang["kv_dur"], _code(iso_to_human(dur_iso))),
                        (lang["kv_max"], _code(f"{config.MAX_DURATION_SECONDS // 60} min")),
                    ]),
                )
                return
            songs = [_pack(url, title, dur_iso, thumb)]

    res = add_songs_to_playlist(user_id, name, songs, config.PLAYLIST_SONG_LIMIT)

    if res is None:
        text = rich_heading(lang["pl_nodb_title"], level=3) + rich_note(lang["pl_nodb_note"])
    elif res["added"] == 0:
        if res["full"]:
            text = (
                rich_heading(lang["pl_full_title"], level=3)
                + rich_note(lang["pl_full_note"].format(config.PLAYLIST_SONG_LIMIT))
            )
        else:
            text = (
                rich_heading(lang["pl_dupe_title"], level=3)
                + rich_note(lang["pl_dupe_note"].format(rich_esc(name)))
            )
    else:
        rows = [(lang["pl_kv_playlist"], _code(name))]
        if len(songs) == 1:
            rows.append((lang["kv_title"], _code(short(songs[0]["title"], 40))))
            rows.append((lang["kv_dur"],   _code(songs[0]["duration"])))
        rows.append((lang["pl_kv_added"], _code(res["added"])))
        skipped = res["dupes"] + skipped_long
        if skipped:
            rows.append((lang["pl_kv_skipped"], _code(skipped)))
        rows.append((lang["pl_kv_total"], _code(f"{res['total']}/{config.PLAYLIST_SONG_LIMIT}")))
        text = rich_heading(lang["pl_added_title"], level=3) + rich_kv_table(rows)
        if res["full"]:
            text += rich_note(lang["pl_full_note"].format(config.PLAYLIST_SONG_LIMIT))

    if pm is not None:
        await rich_edit(pm, text)
    else:
        await rich_send(bot, chat_id, text)


# ── /premove ───────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("premove") & group_allowed & user_allowed)
async def premove_cmd(_, message: Message) -> None:
    lang = chat_strings(message.chat.id)
    if not message.from_user:
        return

    args = _parts(message, 2)
    if len(args) < 2 or not args[1].strip().isdigit():
        await _reply(message, lang["pl_remove_usage_title"], lang["pl_remove_usage_note"])
        return

    if not await _db_ok(message, lang):
        return
    pl = await _get_pl(message, lang, args[0])
    if pl is None:
        return

    total = len(pl.get("songs", []))
    num   = int(args[1].strip())
    if num < 1 or num > total:
        if total == 0:
            await _reply(message, lang["pl_empty_title"], lang["pl_empty_note"].format(rich_esc(pl["name"])))
        else:
            await _reply(message, lang["pl_bad_index_title"], lang["pl_bad_index_note"].format(total))
        return

    removed = remove_song_from_playlist(message.from_user.id, pl["name"], num - 1)
    if removed is None:
        await _reply(message, lang["pl_bad_index_title"], lang["pl_bad_index_note"].format(total))
        return

    await _reply(
        message, lang["pl_removed_title"], rows=[
            (lang["pl_kv_playlist"], _code(pl["name"])),
            (lang["kv_title"],       _code(short(removed.get("title", "?"), 40))),
            (lang["pl_kv_total"],    _code(f"{total - 1}/{config.PLAYLIST_SONG_LIMIT}")),
        ],
    )


# ── /pview ─────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("pview") & group_allowed & user_allowed)
async def pview_cmd(_, message: Message) -> None:
    lang = chat_strings(message.chat.id)
    if not message.from_user:
        return
    if not await _db_ok(message, lang):
        return

    args = _parts(message, 2)

    # /pview -> all playlists of this user
    if not args:
        lists = get_user_playlists(message.from_user.id)
        if not lists:
            await _reply(message, lang["pl_view_empty_title"], lang["pl_view_empty_note"])
            return
        rows = [
            (i, _code(p["name"]), len(p.get("songs", [])))
            for i, p in enumerate(lists, 1)
        ]
        await rich_send(
            bot, message.chat.id,
            rich_heading(lang["pl_view_title"], level=3)
            + rich_table(["#", lang["pl_kv_playlist"], lang["kv_songs"]], rows)
            + rich_note(lang["pl_view_note"]),
        )
        return

    # /pview <name> [page]
    pl = await _get_pl(message, lang, args[0])
    if pl is None:
        return

    songs = pl.get("songs", [])
    if not songs:
        await _reply(message, lang["pl_empty_title"], lang["pl_empty_note"].format(rich_esc(pl["name"])))
        return

    pages = max(1, math.ceil(len(songs) / _PAGE_SIZE))
    try:
        page = int(args[1].strip()) if len(args) > 1 else 1
    except ValueError:
        page = 1
    page = min(max(page, 1), pages)

    start = (page - 1) * _PAGE_SIZE
    rows = [
        (start + i, rich_esc(short(s.get("title", "?"), 38)), s.get("duration", "?"))
        for i, s in enumerate(songs[start:start + _PAGE_SIZE], 1)
    ]

    text = (
        rich_heading(f"{lang['pl_songs_title']} · {rich_esc(pl['name'])}", level=3)
        + rich_table(["#", lang["kv_title"], lang["kv_dur"]], rows)
        + rich_note(lang["pl_page_note"].format(page, pages, len(songs), rich_esc(pl["name"])))
    )
    await rich_send(bot, message.chat.id, text)


# ── /pplay ─────────────────────────────────────────────────────────────────────

@bot.on_message(filters.group & filters.command(["pplay", "cpplay"]) & group_allowed & user_allowed)
async def pplay_cmd(_, message: Message) -> None:
    chat_id = await target_chat(message)      # group, or the linked channel for /cpplay
    if chat_id is None:
        return
    lang = chat_strings(chat_id)
    if not message.from_user:
        return

    args = _parts(message, 1)
    if not args:
        await _reply(message, lang["pl_play_usage_title"], lang["pl_play_usage_note"])
        return
    if not await _db_ok(message, lang):
        return

    pl = await _get_pl(message, lang, args[0].split()[0])
    if pl is None:
        return

    songs = pl.get("songs", [])
    if not songs:
        await _reply(message, lang["pl_empty_title"], lang["pl_empty_note"].format(rich_esc(pl["name"])))
        return

    try:
        add_served_chat(message.chat.id)
    except Exception:
        pass

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
        ok = await try_join_assistant(chat_id, pm)
        if not ok:
            return
        await rich_edit(
            pm,
            rich_heading(lang["play_assistant_joined_title"], level=3)
            + rich_note(lang["generic_processing_note"]),
        )

    req    = message.from_user.first_name or "Unknown"
    req_id = message.from_user.id

    first_was_empty = queue_size(chat_id) == 0

    for s in songs:
        add_to_queue(chat_id, {
            "url":              s["url"],
            "title":            s.get("title", "Unknown"),
            "duration":         s.get("duration", "?"),
            "duration_seconds": s.get("duration_seconds", 0),
            "requester":        req,
            "requester_id":     req_id,
            "thumbnail":        s.get("thumbnail", ""),
            "video":            False,
        })

    rows = [
        (lang["pl_kv_playlist"], _code(pl["name"])),
        (lang["kv_songs"],       _code(len(songs))),
        (lang["kv_first"],       _code(short(songs[0].get("title", "?")))),
    ]
    if len(songs) > 1:
        rows.append((lang["kv_next"], _code(short(songs[1].get("title", "?")))))

    await rich_send(
        bot, chat_id,
        rich_heading(lang["play_playlist_added_title"], level=3) + rich_kv_table(rows),
    )

    if first_was_empty:
        first_song = peek_current(chat_id)
        if first_song:
            await play_song(chat_id, pm, first_song)
    else:
        try:
            await pm.delete()
        except Exception:
            pass


# ── /pdelete ───────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("pdelete") & group_allowed & user_allowed)
async def pdelete_cmd(_, message: Message) -> None:
    lang = chat_strings(message.chat.id)
    if not message.from_user:
        return

    args = _parts(message, 1)
    if not args:
        await _reply(message, lang["pl_delete_usage_title"], lang["pl_delete_usage_note"])
        return
    if not await _db_ok(message, lang):
        return

    pl = await _get_pl(message, lang, args[0].split()[0])
    if pl is None:
        return

    delete_playlist(message.from_user.id, pl["name"])
    await _reply(
        message, lang["pl_deleted_title"],
        lang["pl_deleted_note"].format(rich_esc(pl["name"]), len(pl.get("songs", []))),
    )

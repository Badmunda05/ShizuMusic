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
from ShizuMusic.core.autoplay import (
    AUTOPLAY_LANGS,
    AUTOPLAY_MOODS,
    get_autoplay_lang,
    get_autoplay_mood,
    is_autoplay,
    set_autoplay_lang,
    set_autoplay_mood,
    start_autoplay,
    stop_autoplay,
)
from ShizuMusic.modules.block import group_allowed, user_allowed
from ShizuMusic.utils.language import chat_strings
from ShizuMusic.utils.permissions import is_user_authorized
from richgram import (
    rich_esc,
    rich_heading,
    rich_kv_table,
    rich_note,
    rich_send,
)


def _status_table(lang: dict, chat_id: int) -> str:
    on = is_autoplay(chat_id)
    song_lang = get_autoplay_lang(chat_id)
    mood = get_autoplay_mood(chat_id)
    return rich_kv_table([
        (lang["autoplay_kv_status"], lang["autoplay_status_on"] if on else lang["autoplay_status_off"]),
        (lang["autoplay_kv_lang"], f"<code>{rich_esc(song_lang)}</code>"),
        (lang["autoplay_kv_mood"], f"<code>{rich_esc(mood)}</code>"),
    ])


@bot.on_message(
    filters.group
    & filters.command(["autoplay", "cautoplay"])
    & group_allowed
    & user_allowed
)
async def autoplay_cmd(_, message: Message) -> None:

    chat_id = await target_chat(message)
    if chat_id is None:
        return
    lang = chat_strings(chat_id)   # this chat's chosen strings/langs/*.yml
    args = [a.lower() for a in message.command[1:]]

    # /autoplay -> just show current settings
    if not args:
        await rich_send(
            bot, chat_id,
            rich_heading(lang["autoplay_title"], level=3)
            + _status_table(lang, chat_id)
            + rich_note(
                lang["autoplay_status_note"].format(
                    ", ".join(AUTOPLAY_LANGS),
                    ", ".join(AUTOPLAY_MOODS),
                )
            ),
        )
        return

    if not await is_user_authorized(message):
        await rich_send(
            bot, chat_id,
            rich_heading(lang["autoplay_admin_only_title"], level=3)
            + rich_note(lang["autoplay_admin_only_note"]),
        )
        return

    action = args[0]
    who = message.from_user.mention if message.from_user else lang["autoplay_someone"]

    if action in ("on", "enable", "start"):
        start_autoplay(chat_id)
        await rich_send(
            bot, chat_id,
            rich_heading(lang["autoplay_enabled_title"], level=3)
            + rich_note(lang["autoplay_enabled_note"].format(who)),
        )
        return

    if action in ("off", "disable", "stop"):
        stop_autoplay(chat_id)
        await rich_send(
            bot, chat_id,
            rich_heading(lang["autoplay_disabled_title"], level=3)
            + rich_note(lang["autoplay_disabled_note"].format(who)),
        )
        return

    if action in ("lang", "language") and len(args) >= 2:
        song_lang = args[1]
        if song_lang not in AUTOPLAY_LANGS:
            await rich_send(
                bot, chat_id,
                rich_heading(lang["autoplay_unknown_lang_title"], level=3)
                + rich_note(lang["autoplay_unknown_lang_note"].format(", ".join(AUTOPLAY_LANGS))),
            )
            return
        set_autoplay_lang(chat_id, song_lang)
        await rich_send(
            bot, chat_id,
            rich_heading(lang["autoplay_lang_set_title"], level=3)
            + rich_note(lang["autoplay_lang_set_note"].format(rich_esc(song_lang))),
        )
        return

    if action == "mood" and len(args) >= 2:
        mood = args[1]
        if mood not in AUTOPLAY_MOODS:
            await rich_send(
                bot, chat_id,
                rich_heading(lang["autoplay_unknown_mood_title"], level=3)
                + rich_note(lang["autoplay_unknown_mood_note"].format(", ".join(AUTOPLAY_MOODS))),
            )
            return
        set_autoplay_mood(chat_id, mood)
        await rich_send(
            bot, chat_id,
            rich_heading(lang["autoplay_mood_set_title"], level=3)
            + rich_note(lang["autoplay_mood_set_note"].format(rich_esc(mood))),
        )
        return

    await rich_send(
        bot, chat_id,
        rich_heading(lang["autoplay_usage_title"], level=3)
        + rich_note(lang["autoplay_usage_note"]),
    )

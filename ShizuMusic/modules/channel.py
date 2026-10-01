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
#
#  Channel play
#
#    /addchannel <@username | -100id>   link a channel to this group   (admins)
#    /addchannel                        show what is linked right now
#    /delchannel                        stop channel playback + unlink  (admins)
#
#  Once linked, every playback command has a "c" twin that drives the
#  CHANNEL's voice chat (its own queue, effects and autoplay), while the
#  panels and replies stay in this group:
#
#    /cplay /cvplay /cplayforce /cvplayforce /cpplay
#    /cpause /cresume /cskip /cstop /cend /cclear
#    /cseek /cseekback /cspeed /cspeedreset /cbass /cbassoff
#    /ceffecton /ceffectoff /ceffects /cautoplay /cthumbnail
#
#  The bot must be an ADMIN of the channel (it needs the invite-link right to
#  bring the assistant in) and whoever links it must be an admin there too.
# --------------------------------------------------------------------------------

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.types import Message

import config
from ShizuMusic import bot
from ShizuMusic.core.call import leave_vc
from ShizuMusic.modules.block import group_allowed, user_allowed
from ShizuMusic.utils.db import (
    get_channel_link_owner,
    remove_channel_link,
    set_channel_link,
)
from ShizuMusic.utils.language import chat_strings
from ShizuMusic.utils.permissions import is_user_authorized
from richgram import (
    rich_esc,
    rich_heading,
    rich_kv_table,
    rich_note,
    rich_send,
)
from ShizuMusic.utils.routes import group_channel, register_link, unregister_group

_ADMIN = (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)


def _clean_ref(ref: str):
    """'@name' / 't.me/name' / 'https://t.me/name' / '-100123' -> name or int id."""
    ref = ref.strip()
    for prefix in ("https://t.me/", "http://t.me/", "t.me/"):
        if ref.lower().startswith(prefix):
            ref = ref[len(prefix):]
            break
    ref = ref.lstrip("@").split("/")[0].split("?")[0]
    if ref.lstrip("-").isdigit():
        return int(ref)
    return ref


async def _say(chat_id: int, title: str, note: str = "", rows=None) -> None:
    body = rich_heading(title, level=3)
    if rows:
        body += rich_kv_table(rows)
    if note:
        body += rich_note(note)
    await rich_send(bot, chat_id, body)


# ── /addchannel ────────────────────────────────────────────────────────────────

@bot.on_message(
    filters.group
    & filters.command(["addchannel", "setchannel"])
    & group_allowed
    & user_allowed
)
async def addchannel_cmd(_, message: Message) -> None:

    group_id = message.chat.id
    lang = chat_strings(group_id)
    args = message.command[1:]

    # /addchannel -> status
    if not args:
        channel_id = group_channel.get(group_id)
        if channel_id is None:
            await _say(group_id, lang["ch_status_title"], lang["ch_status_none_note"])
            return
        try:
            chat = await bot.get_chat(channel_id)
            title = rich_esc(chat.title)
        except Exception:
            title = "?"
        await _say(
            group_id, lang["ch_status_title"], lang["ch_status_usage_note"],
            rows=[
                (lang["kv_chat_title"], title),
                (lang["kv_chat_id"], f"<code>{channel_id}</code>"),
            ],
        )
        return

    if not await is_user_authorized(message):
        await _say(group_id, lang["admin_only_title"], lang["admin_only_note"])
        return

    user = message.from_user
    if not user:
        return

    # ── find the channel ────────────────────────────────────────────────────────
    try:
        chat = await bot.get_chat(_clean_ref(args[0]))
    except Exception:
        await _say(group_id, lang["ch_not_found_title"], lang["ch_not_found_note"])
        return

    if chat.type != ChatType.CHANNEL:
        await _say(group_id, lang["ch_not_channel_title"], lang["ch_not_channel_note"])
        return

    # ── the bot must be an admin there ──────────────────────────────────────────
    try:
        me = await bot.get_me()
        bm = await bot.get_chat_member(chat.id, me.id)
    except Exception:
        await _say(group_id, lang["ch_bot_missing_title"], lang["ch_bot_missing_note"])
        return

    if bm.status not in _ADMIN:
        await _say(group_id, lang["ch_bot_missing_title"], lang["ch_bot_missing_note"])
        return

    # ── and so must the person linking it ───────────────────────────────────────
    if user.id != config.OWNER_ID:
        try:
            um = await bot.get_chat_member(chat.id, user.id)
            is_admin = um.status in _ADMIN
        except Exception:
            is_admin = False
        if not is_admin:
            await _say(group_id, lang["ch_user_not_admin_title"], lang["ch_user_not_admin_note"])
            return

    # ── one channel <-> one group ───────────────────────────────────────────────
    other = get_channel_link_owner(chat.id)
    if other is not None and other != group_id:
        await _say(group_id, lang["ch_taken_title"], lang["ch_taken_note"])
        return

    # switching to a different channel: stop what the old one was playing
    old = group_channel.get(group_id)
    if old is not None and old != chat.id:
        await leave_vc(old)

    set_channel_link(group_id, chat.id)
    register_link(group_id, chat.id)

    await _say(
        group_id, lang["ch_linked_title"], lang["ch_linked_note"],
        rows=[
            (lang["kv_chat_title"], rich_esc(chat.title)),
            (lang["kv_chat_id"], f"<code>{chat.id}</code>"),
        ],
    )


# ── /delchannel ────────────────────────────────────────────────────────────────

@bot.on_message(
    filters.group
    & filters.command(["delchannel", "removechannel"])
    & group_allowed
    & user_allowed
)
async def delchannel_cmd(_, message: Message) -> None:

    group_id = message.chat.id
    lang = chat_strings(group_id)

    if not await is_user_authorized(message):
        await _say(group_id, lang["admin_only_title"], lang["admin_only_note"])
        return

    channel_id = group_channel.get(group_id)
    if channel_id is None:
        await _say(group_id, lang["ch_not_linked_title"], lang["ch_not_linked_note"])
        return

    await leave_vc(channel_id)            # stop playback + clear the channel's queue
    remove_channel_link(group_id)
    unregister_group(group_id)

    await _say(group_id, lang["ch_unlinked_title"], lang["ch_unlinked_note"])

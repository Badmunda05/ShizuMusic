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
from ShizuMusic.utils.db import (
    block_group,
    unblock_group,
    is_group_blocked,
    get_blocked_groups,
    block_user,
    unblock_user,
    is_user_blocked_db,
    get_blocked_users,
)
from ShizuMusic.utils.language import chat_strings
from richgram import (
    rich_esc,
    rich_heading,
    rich_kv_table,
    rich_note,
    rich_send,
    sanitize_display_name,
)


# ── Pyrogram filters (import these in other modules) ──────────────────────────

def _group_not_blocked(_, __, message: Message) -> bool:
    if message.chat and message.chat.id:
        return not is_group_blocked(message.chat.id)
    return True


def _user_not_blocked(_, __, message: Message) -> bool:
    if message.from_user and message.from_user.id:
        return not is_user_blocked_db(message.from_user.id)
    return True


group_allowed = filters.create(_group_not_blocked)
user_allowed  = filters.create(_user_not_blocked)


# ── /gblock ────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("gblock") & filters.user(config.OWNER_ID))
async def gblock_cmd(_, message: Message) -> None:
    """Block a group — /gblock or /gblock -100xxxxxxx"""
    chat_id = message.chat.id
    lang = chat_strings(chat_id)
    args = message.command[1:]

    if args:
        try:
            chat_id = int(args[0])
        except ValueError:
            await rich_send(
                bot, chat_id,
                rich_heading(lang["block_invalid_chat_id_title"], level=3)
                + rich_kv_table([(lang["kv_usage"], "<code>/gblock -100xxxxxxx</code>")]),
            )
            return
    else:
        if message.chat.type.name == "PRIVATE":
            await rich_send(
                bot, chat_id,
                rich_heading(lang["block_use_group_or_id_title"], level=3)
                + rich_kv_table([(lang["kv_usage"], "<code>/gblock -100xxxxxxx</code>")]),
            )
            return
        chat_id = message.chat.id

    if is_group_blocked(chat_id):
        await rich_send(
            bot, message.chat.id,
            rich_heading(lang["block_already_title"], level=3)
            + rich_kv_table([(lang["kv_group"], f"<code>{chat_id}</code>")]),
        )
        return

    block_group(chat_id)
    await rich_send(
        bot, message.chat.id,
        rich_heading(lang["block_group_blocked_title"], level=3)
        + rich_kv_table([(lang["kv_chat_id"], f"<code>{chat_id}</code>")])
        + rich_note(lang["block_group_blocked_note"]),
    )


# ── /gunblock ──────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("gunblock") & filters.user(config.OWNER_ID))
async def gunblock_cmd(_, message: Message) -> None:
    """Unblock a group — /gunblock or /gunblock -100xxxxxxx"""
    chat_id = message.chat.id
    lang = chat_strings(chat_id)
    args = message.command[1:]

    if args:
        try:
            chat_id = int(args[0])
        except ValueError:
            await rich_send(
                bot, chat_id,
                rich_heading(lang["block_invalid_chat_id_title"], level=3)
                + rich_kv_table([(lang["kv_usage"], "<code>/gunblock -100xxxxxxx</code>")]),
            )
            return
    else:
        if message.chat.type.name == "PRIVATE":
            await rich_send(
                bot, chat_id,
                rich_heading(lang["block_use_group_or_id_title"], level=3)
                + rich_kv_table([(lang["kv_usage"], "<code>/gunblock -100xxxxxxx</code>")]),
            )
            return
        chat_id = message.chat.id

    if not is_group_blocked(chat_id):
        await rich_send(
            bot, message.chat.id,
            rich_heading(lang["block_not_blocked_title"], level=3)
            + rich_kv_table([(lang["kv_group"], f"<code>{chat_id}</code>")]),
        )
        return

    unblock_group(chat_id)
    await rich_send(
        bot, message.chat.id,
        rich_heading(lang["block_group_unblocked_title"], level=3)
        + rich_kv_table([(lang["kv_chat_id"], f"<code>{chat_id}</code>")])
        + rich_note(lang["block_group_unblocked_note"]),
    )


# ── /ublock ────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("ublock") & filters.user(config.OWNER_ID))
async def ublock_cmd(_, message: Message) -> None:
    """Block a user — reply to their message or /ublock 123456789"""
    chat_id   = message.chat.id
    lang      = chat_strings(chat_id)
    args      = message.command[1:]
    user_id   = None
    user_name = None

    if message.reply_to_message and message.reply_to_message.from_user:
        user_id   = message.reply_to_message.from_user.id
        user_name = sanitize_display_name(message.reply_to_message.from_user.first_name)
    elif args:
        try:
            user_id = int(args[0])
        except ValueError:
            await rich_send(
                bot, chat_id,
                rich_heading(lang["block_invalid_user_id_title"], level=3)
                + rich_note(lang["block_ublock_usage_note"]),
            )
            return
    else:
        await rich_send(
            bot, chat_id,
            rich_heading(lang["block_reply_or_id_title"], level=3)
            + rich_kv_table([(lang["kv_usage"], "<code>/ublock 123456789</code>")]),
        )
        return

    if user_id == config.OWNER_ID:
        await rich_send(bot, chat_id, rich_heading(lang["block_cannot_block_owner_title"], level=3))
        return

    if is_user_blocked_db(user_id):
        await rich_send(
            bot, chat_id,
            rich_heading(lang["block_already_title"], level=3)
            + rich_kv_table([(lang["kv_user"], f"<code>{user_id}</code>")]),
        )
        return

    block_user(user_id)
    rows = [(lang["kv_user_id"], f"<code>{user_id}</code>")]
    if user_name:
        rows.append((lang["kv_name"], rich_esc(user_name)))
    await rich_send(
        bot, chat_id,
        rich_heading(lang["block_user_blocked_title"], level=3)
        + rich_kv_table(rows)
        + rich_note(lang["block_user_blocked_note"]),
    )


# ── /uunblock ──────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("uunblock") & filters.user(config.OWNER_ID))
async def uunblock_cmd(_, message: Message) -> None:
    """Unblock a user — reply to their message or /uunblock 123456789"""
    chat_id   = message.chat.id
    lang      = chat_strings(chat_id)
    args      = message.command[1:]
    user_id   = None
    user_name = None

    if message.reply_to_message and message.reply_to_message.from_user:
        user_id   = message.reply_to_message.from_user.id
        user_name = sanitize_display_name(message.reply_to_message.from_user.first_name)
    elif args:
        try:
            user_id = int(args[0])
        except ValueError:
            await rich_send(
                bot, chat_id,
                rich_heading(lang["block_invalid_user_id_title"], level=3)
                + rich_note(lang["block_uunblock_usage_note"]),
            )
            return
    else:
        await rich_send(
            bot, chat_id,
            rich_heading(lang["block_reply_or_id_title"], level=3)
            + rich_kv_table([(lang["kv_usage"], "<code>/uunblock 123456789</code>")]),
        )
        return

    if not is_user_blocked_db(user_id):
        await rich_send(
            bot, chat_id,
            rich_heading(lang["block_not_blocked_title"], level=3)
            + rich_kv_table([(lang["kv_user"], f"<code>{user_id}</code>")]),
        )
        return

    unblock_user(user_id)
    rows = [(lang["kv_user_id"], f"<code>{user_id}</code>")]
    if user_name:
        rows.append((lang["kv_name"], rich_esc(user_name)))
    await rich_send(
        bot, chat_id,
        rich_heading(lang["block_user_unblocked_title"], level=3)
        + rich_kv_table(rows)
        + rich_note(lang["block_user_unblocked_note"]),
    )


# ── /blocklist ─────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("blocklist") & filters.user(config.OWNER_ID))
async def blocklist_cmd(_, message: Message) -> None:
    """Show all blocked groups and users."""
    lang   = chat_strings(message.chat.id)
    groups = get_blocked_groups()
    users  = get_blocked_users()

    rows = [(lang["kv_group"], f"<code>{g}</code>") for g in groups]
    rows += [(lang["kv_user"], f"<code>{u}</code>") for u in users]

    content = rich_heading(lang["block_list_title"].format(len(groups), len(users)), level=3)
    if rows:
        content += rich_kv_table(rows, headers=[lang["kv_type"], lang["kv_id"]])
    else:
        content += rich_note(lang["block_list_empty_note"])

    await rich_send(bot, message.chat.id, content)

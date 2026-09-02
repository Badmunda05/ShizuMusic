# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

from pyrogram import filters
from pyrogram.enums import ParseMode
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
    args = message.command[1:]

    if args:
        try:
            chat_id = int(args[0])
        except ValueError:
            await message.reply(
                "<b>❍ Invalid chat ID.</b>\n"
                "<b>❍ Usage: /gblock -100xxxxxxx</b>",
                parse_mode=ParseMode.HTML,
            )
            return
    else:
        if message.chat.type.name == "PRIVATE":
            await message.reply(
                "<b>❍ Use in a group or provide a chat ID.</b>\n"
                "<b>❍ Usage: /gblock -100xxxxxxx</b>",
                parse_mode=ParseMode.HTML,
            )
            return
        chat_id = message.chat.id

    if is_group_blocked(chat_id):
        await message.reply(
            f"<b>❍ Group <code>{chat_id}</code> is already blocked.</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    block_group(chat_id)
    await message.reply(
        f"<b>❍ Group Blocked ✅</b>\n"
        f"<b>❍ Chat ID :</b> <code>{chat_id}</code>\n"
        f"<b>❍ No commands will work in this group now.</b>",
        parse_mode=ParseMode.HTML,
    )


# ── /gunblock ──────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("gunblock") & filters.user(config.OWNER_ID))
async def gunblock_cmd(_, message: Message) -> None:
    """Unblock a group — /gunblock or /gunblock -100xxxxxxx"""
    args = message.command[1:]

    if args:
        try:
            chat_id = int(args[0])
        except ValueError:
            await message.reply(
                "<b>❍ Invalid chat ID.</b>\n"
                "<b>❍ Usage: /gunblock -100xxxxxxx</b>",
                parse_mode=ParseMode.HTML,
            )
            return
    else:
        if message.chat.type.name == "PRIVATE":
            await message.reply(
                "<b>❍ Use in a group or provide a chat ID.</b>\n"
                "<b>❍ Usage: /gunblock -100xxxxxxx</b>",
                parse_mode=ParseMode.HTML,
            )
            return
        chat_id = message.chat.id

    if not is_group_blocked(chat_id):
        await message.reply(
            f"<b>❍ Group <code>{chat_id}</code> is not blocked.</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    unblock_group(chat_id)
    await message.reply(
        f"<b>❍ Group Unblocked ✅</b>\n"
        f"<b>❍ Chat ID :</b> <code>{chat_id}</code>\n"
        f"<b>❍ Commands are now enabled in this group.</b>",
        parse_mode=ParseMode.HTML,
    )


# ── /ublock ────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("ublock") & filters.user(config.OWNER_ID))
async def ublock_cmd(_, message: Message) -> None:
    """Block a user — reply to their message or /ublock 123456789"""
    args      = message.command[1:]
    user_id   = None
    user_name = None

    if message.reply_to_message and message.reply_to_message.from_user:
        user_id   = message.reply_to_message.from_user.id
        user_name = message.reply_to_message.from_user.first_name
    elif args:
        try:
            user_id = int(args[0])
        except ValueError:
            await message.reply(
                "<b>❍ Invalid user ID.</b>\n"
                "<b>❍ Usage: /ublock 123456789 or reply to a user.</b>",
                parse_mode=ParseMode.HTML,
            )
            return
    else:
        await message.reply(
            "<b>❍ Reply to a user's message or provide a user ID.</b>\n"
            "<b>❍ Usage: /ublock 123456789</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    if user_id == config.OWNER_ID:
        await message.reply(
            "<b>❍ You cannot block yourself (owner).</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    if is_user_blocked_db(user_id):
        await message.reply(
            f"<b>❍ User <code>{user_id}</code> is already blocked.</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    block_user(user_id)
    name_str = f" (<b>{user_name}</b>)" if user_name else ""
    await message.reply(
        f"<b>❍ User Blocked ✅</b>\n"
        f"<b>❍ User ID :</b> <code>{user_id}</code>{name_str}\n"
        f"<b>❍ This user cannot use any bot commands now.</b>",
        parse_mode=ParseMode.HTML,
    )


# ── /uunblock ──────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("uunblock") & filters.user(config.OWNER_ID))
async def uunblock_cmd(_, message: Message) -> None:
    """Unblock a user — reply to their message or /uunblock 123456789"""
    args      = message.command[1:]
    user_id   = None
    user_name = None

    if message.reply_to_message and message.reply_to_message.from_user:
        user_id   = message.reply_to_message.from_user.id
        user_name = message.reply_to_message.from_user.first_name
    elif args:
        try:
            user_id = int(args[0])
        except ValueError:
            await message.reply(
                "<b>❍ Invalid user ID.</b>\n"
                "<b>❍ Usage: /uunblock 123456789 or reply to a user.</b>",
                parse_mode=ParseMode.HTML,
            )
            return
    else:
        await message.reply(
            "<b>❍ Reply to a user's message or provide a user ID.</b>\n"
            "<b>❍ Usage: /uunblock 123456789</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    if not is_user_blocked_db(user_id):
        await message.reply(
            f"<b>❍ User <code>{user_id}</code> is not blocked.</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    unblock_user(user_id)
    name_str = f" (<b>{user_name}</b>)" if user_name else ""
    await message.reply(
        f"<b>❍ User Unblocked ✅</b>\n"
        f"<b>❍ User ID :</b> <code>{user_id}</code>{name_str}\n"
        f"<b>❍ This user can now use bot commands again.</b>",
        parse_mode=ParseMode.HTML,
    )


# ── /blocklist ─────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("blocklist") & filters.user(config.OWNER_ID))
async def blocklist_cmd(_, message: Message) -> None:
    """Show all blocked groups and users."""
    groups = get_blocked_groups()
    users  = get_blocked_users()

    g_text = (
        "\n".join(f"  • <code>{g}</code>" for g in groups)
        if groups else "  None"
    )
    u_text = (
        "\n".join(f"  • <code>{u}</code>" for u in users)
        if users else "  None"
    )

    await message.reply(
        "<b>❍ Block List</b>\n\n"
        f"<b>❍ Blocked Groups ({len(groups)}):</b>\n{g_text}\n\n"
        f"<b>❍ Blocked Users ({len(users)}):</b>\n{u_text}",
        parse_mode=ParseMode.HTML,
    )
    

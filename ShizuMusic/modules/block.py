# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

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
from ShizuMusic.utils.rich_ui import (
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
    args = message.command[1:]

    if args:
        try:
            chat_id = int(args[0])
        except ValueError:
            await rich_send(
                bot, chat_id,
                rich_heading("❍ ɪɴᴠᴀʟɪᴅ ᴄʜᴀᴛ ɪᴅ", level=3)
                + rich_kv_table([("ᴜsᴀɢᴇ", "<code>/gblock -100xxxxxxx</code>")]),
            )
            return
    else:
        if message.chat.type.name == "PRIVATE":
            await rich_send(
                bot, chat_id,
                rich_heading("❍ ᴜsᴇ ɪɴ ᴀ ɢʀᴏᴜᴘ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴄʜᴀᴛ ɪᴅ", level=3)
                + rich_kv_table([("ᴜsᴀɢᴇ", "<code>/gblock -100xxxxxxx</code>")]),
            )
            return
        chat_id = message.chat.id

    if is_group_blocked(chat_id):
        await rich_send(
            bot, message.chat.id,
            rich_heading("❍ ᴀʟʀᴇᴀᴅʏ ʙʟᴏᴄᴋᴇᴅ", level=3)
            + rich_kv_table([("ɢʀᴏᴜᴘ", f"<code>{chat_id}</code>")]),
        )
        return

    block_group(chat_id)
    await rich_send(
        bot, message.chat.id,
        rich_heading("❍ ɢʀᴏᴜᴘ ʙʟᴏᴄᴋᴇᴅ ✅", level=3)
        + rich_kv_table([("ᴄʜᴀᴛ ɪᴅ", f"<code>{chat_id}</code>")])
        + rich_note("ɴᴏ ᴄᴏᴍᴍᴀɴᴅs ᴡɪʟʟ ᴡᴏʀᴋ ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ ɴᴏᴡ."),
    )


# ── /gunblock ──────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("gunblock") & filters.user(config.OWNER_ID))
async def gunblock_cmd(_, message: Message) -> None:
    """Unblock a group — /gunblock or /gunblock -100xxxxxxx"""
    chat_id = message.chat.id
    args = message.command[1:]

    if args:
        try:
            chat_id = int(args[0])
        except ValueError:
            await rich_send(
                bot, chat_id,
                rich_heading("❍ ɪɴᴠᴀʟɪᴅ ᴄʜᴀᴛ ɪᴅ", level=3)
                + rich_kv_table([("ᴜsᴀɢᴇ", "<code>/gunblock -100xxxxxxx</code>")]),
            )
            return
    else:
        if message.chat.type.name == "PRIVATE":
            await rich_send(
                bot, chat_id,
                rich_heading("❍ ᴜsᴇ ɪɴ ᴀ ɢʀᴏᴜᴘ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴄʜᴀᴛ ɪᴅ", level=3)
                + rich_kv_table([("ᴜsᴀɢᴇ", "<code>/gunblock -100xxxxxxx</code>")]),
            )
            return
        chat_id = message.chat.id

    if not is_group_blocked(chat_id):
        await rich_send(
            bot, message.chat.id,
            rich_heading("❍ ɴᴏᴛ ʙʟᴏᴄᴋᴇᴅ", level=3)
            + rich_kv_table([("ɢʀᴏᴜᴘ", f"<code>{chat_id}</code>")]),
        )
        return

    unblock_group(chat_id)
    await rich_send(
        bot, message.chat.id,
        rich_heading("❍ ɢʀᴏᴜᴘ ᴜɴʙʟᴏᴄᴋᴇᴅ ✅", level=3)
        + rich_kv_table([("ᴄʜᴀᴛ ɪᴅ", f"<code>{chat_id}</code>")])
        + rich_note("ᴄᴏᴍᴍᴀɴᴅs ᴀʀᴇ ɴᴏᴡ ᴇɴᴀʙʟᴇᴅ ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ."),
    )


# ── /ublock ────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("ublock") & filters.user(config.OWNER_ID))
async def ublock_cmd(_, message: Message) -> None:
    """Block a user — reply to their message or /ublock 123456789"""
    chat_id   = message.chat.id
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
                rich_heading("❍ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ", level=3)
                + rich_note("ᴜsᴇ » <code>/ublock 123456789</code> ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ."),
            )
            return
    else:
        await rich_send(
            bot, chat_id,
            rich_heading("❍ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ's ᴍᴇssᴀɢᴇ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴜsᴇʀ ɪᴅ", level=3)
            + rich_kv_table([("ᴜsᴀɢᴇ", "<code>/ublock 123456789</code>")]),
        )
        return

    if user_id == config.OWNER_ID:
        await rich_send(bot, chat_id, rich_heading("❍ ʏᴏᴜ ᴄᴀɴɴᴏᴛ ʙʟᴏᴄᴋ ʏᴏᴜʀsᴇʟғ (ᴏᴡɴᴇʀ)", level=3))
        return

    if is_user_blocked_db(user_id):
        await rich_send(
            bot, chat_id,
            rich_heading("❍ ᴀʟʀᴇᴀᴅʏ ʙʟᴏᴄᴋᴇᴅ", level=3)
            + rich_kv_table([("ᴜsᴇʀ", f"<code>{user_id}</code>")]),
        )
        return

    block_user(user_id)
    rows = [("ᴜsᴇʀ ɪᴅ", f"<code>{user_id}</code>")]
    if user_name:
        rows.append(("ɴᴀᴍᴇ", rich_esc(user_name)))
    await rich_send(
        bot, chat_id,
        rich_heading("❍ ᴜsᴇʀ ʙʟᴏᴄᴋᴇᴅ ✅", level=3)
        + rich_kv_table(rows)
        + rich_note("ᴛʜɪs ᴜsᴇʀ ᴄᴀɴɴᴏᴛ ᴜsᴇ ᴀɴʏ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs ɴᴏᴡ."),
    )


# ── /uunblock ──────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("uunblock") & filters.user(config.OWNER_ID))
async def uunblock_cmd(_, message: Message) -> None:
    """Unblock a user — reply to their message or /uunblock 123456789"""
    chat_id   = message.chat.id
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
                rich_heading("❍ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ", level=3)
                + rich_note("ᴜsᴇ » <code>/uunblock 123456789</code> ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ."),
            )
            return
    else:
        await rich_send(
            bot, chat_id,
            rich_heading("❍ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ's ᴍᴇssᴀɢᴇ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴜsᴇʀ ɪᴅ", level=3)
            + rich_kv_table([("ᴜsᴀɢᴇ", "<code>/uunblock 123456789</code>")]),
        )
        return

    if not is_user_blocked_db(user_id):
        await rich_send(
            bot, chat_id,
            rich_heading("❍ ɴᴏᴛ ʙʟᴏᴄᴋᴇᴅ", level=3)
            + rich_kv_table([("ᴜsᴇʀ", f"<code>{user_id}</code>")]),
        )
        return

    unblock_user(user_id)
    rows = [("ᴜsᴇʀ ɪᴅ", f"<code>{user_id}</code>")]
    if user_name:
        rows.append(("ɴᴀᴍᴇ", rich_esc(user_name)))
    await rich_send(
        bot, chat_id,
        rich_heading("❍ ᴜsᴇʀ ᴜɴʙʟᴏᴄᴋᴇᴅ ✅", level=3)
        + rich_kv_table(rows)
        + rich_note("ᴛʜɪs ᴜsᴇʀ ᴄᴀɴ ɴᴏᴡ ᴜsᴇ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs ᴀɢᴀɪɴ."),
    )


# ── /blocklist ─────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("blocklist") & filters.user(config.OWNER_ID))
async def blocklist_cmd(_, message: Message) -> None:
    """Show all blocked groups and users."""
    groups = get_blocked_groups()
    users  = get_blocked_users()

    rows = [("ɢʀᴏᴜᴘ", f"<code>{g}</code>") for g in groups]
    rows += [("ᴜsᴇʀ", f"<code>{u}</code>") for u in users]

    content = rich_heading(f"❍ ʙʟᴏᴄᴋ ʟɪsᴛ — {len(groups)} ɢʀᴏᴜᴘs, {len(users)} ᴜsᴇʀs", level=3)
    if rows:
        content += rich_kv_table(rows, headers=["ᴛʏᴘᴇ", "ɪᴅ"])
    else:
        content += rich_note("ɴᴏᴛʜɪɴɢ ɪs ʙʟᴏᴄᴋᴇᴅ.")

    await rich_send(bot, message.chat.id, content)
    

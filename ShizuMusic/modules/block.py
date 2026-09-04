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
    rich_reply,
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
            await rich_reply(
                message,
                rich_heading("❍ ɪɴᴠᴀʟɪᴅ ᴄʜᴀᴛ ɪᴅ", level=3)
                + rich_note("ᴜsᴀɢᴇ » <code>/gblock -100xxxxxxx</code>"),
            )
            return
    else:
        if message.chat.type.name == "PRIVATE":
            await rich_reply(
                message,
                rich_heading("❍ ᴜsᴇ ɪɴ ᴀ ɢʀᴏᴜᴘ", level=3)
                + rich_note("ᴜsᴇ ᴛʜɪs ɪɴ ᴀ ɢʀᴏᴜᴘ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴄʜᴀᴛ ɪᴅ. "
                            "ᴜsᴀɢᴇ » <code>/gblock -100xxxxxxx</code>"),
            )
            return
        chat_id = message.chat.id

    if is_group_blocked(chat_id):
        await rich_reply(
            message,
            rich_heading("❍ ᴀʟʀᴇᴀᴅʏ ʙʟᴏᴄᴋᴇᴅ", level=3)
            + rich_kv_table([("ɢʀᴏᴜᴘ", f"<code>{chat_id}</code>")]),
        )
        return

    block_group(chat_id)
    await rich_reply(
        message,
        rich_heading("✅ ɢʀᴏᴜᴘ ʙʟᴏᴄᴋᴇᴅ", level=3)
        + rich_kv_table([("ᴄʜᴀᴛ ɪᴅ", f"<code>{chat_id}</code>")])
        + rich_note("ɴᴏ ᴄᴏᴍᴍᴀɴᴅs ᴡɪʟʟ ᴡᴏʀᴋ ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ ɴᴏᴡ."),
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
            await rich_reply(
                message,
                rich_heading("❍ ɪɴᴠᴀʟɪᴅ ᴄʜᴀᴛ ɪᴅ", level=3)
                + rich_note("ᴜsᴀɢᴇ » <code>/gunblock -100xxxxxxx</code>"),
            )
            return
    else:
        if message.chat.type.name == "PRIVATE":
            await rich_reply(
                message,
                rich_heading("❍ ᴜsᴇ ɪɴ ᴀ ɢʀᴏᴜᴘ", level=3)
                + rich_note("ᴜsᴇ ᴛʜɪs ɪɴ ᴀ ɢʀᴏᴜᴘ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴄʜᴀᴛ ɪᴅ. "
                            "ᴜsᴀɢᴇ » <code>/gunblock -100xxxxxxx</code>"),
            )
            return
        chat_id = message.chat.id

    if not is_group_blocked(chat_id):
        await rich_reply(
            message,
            rich_heading("❍ ɴᴏᴛ ʙʟᴏᴄᴋᴇᴅ", level=3)
            + rich_kv_table([("ɢʀᴏᴜᴘ", f"<code>{chat_id}</code>")]),
        )
        return

    unblock_group(chat_id)
    await rich_reply(
        message,
        rich_heading("✅ ɢʀᴏᴜᴘ ᴜɴʙʟᴏᴄᴋᴇᴅ", level=3)
        + rich_kv_table([("ᴄʜᴀᴛ ɪᴅ", f"<code>{chat_id}</code>")])
        + rich_note("ᴄᴏᴍᴍᴀɴᴅs ᴀʀᴇ ɴᴏᴡ ᴇɴᴀʙʟᴇᴅ ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ."),
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
            await rich_reply(
                message,
                rich_heading("❍ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ", level=3)
                + rich_note("ᴜsᴀɢᴇ » <code>/ublock 123456789</code> ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ."),
            )
            return
    else:
        await rich_reply(
            message,
            rich_heading("❍ ᴍɪssɪɴɢ ᴛᴀʀɢᴇᴛ", level=3)
            + rich_note("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ's ᴍᴇssᴀɢᴇ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴜsᴇʀ ɪᴅ. "
                        "ᴜsᴀɢᴇ » <code>/ublock 123456789</code>"),
        )
        return

    if user_id == config.OWNER_ID:
        await rich_reply(
            message,
            rich_heading("❍ ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ", level=3)
            + rich_note("ʏᴏᴜ ᴄᴀɴɴᴏᴛ ʙʟᴏᴄᴋ ʏᴏᴜʀsᴇʟғ (ᴏᴡɴᴇʀ)."),
        )
        return

    if is_user_blocked_db(user_id):
        await rich_reply(
            message,
            rich_heading("❍ ᴀʟʀᴇᴀᴅʏ ʙʟᴏᴄᴋᴇᴅ", level=3)
            + rich_kv_table([("ᴜsᴇʀ", f"<code>{user_id}</code>")]),
        )
        return

    block_user(user_id)
    await rich_reply(
        message,
        rich_heading("✅ ᴜsᴇʀ ʙʟᴏᴄᴋᴇᴅ", level=3)
        + rich_kv_table([
            ("ᴜsᴇʀ ɪᴅ", f"<code>{user_id}</code>"),
            ("ɴᴀᴍᴇ", rich_esc(user_name) if user_name else None),
        ])
        + rich_note("ᴛʜɪs ᴜsᴇʀ ᴄᴀɴɴᴏᴛ ᴜsᴇ ᴀɴʏ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs ɴᴏᴡ."),
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
            await rich_reply(
                message,
                rich_heading("❍ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ", level=3)
                + rich_note("ᴜsᴀɢᴇ » <code>/uunblock 123456789</code> ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ."),
            )
            return
    else:
        await rich_reply(
            message,
            rich_heading("❍ ᴍɪssɪɴɢ ᴛᴀʀɢᴇᴛ", level=3)
            + rich_note("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ's ᴍᴇssᴀɢᴇ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴜsᴇʀ ɪᴅ. "
                        "ᴜsᴀɢᴇ » <code>/uunblock 123456789</code>"),
        )
        return

    if not is_user_blocked_db(user_id):
        await rich_reply(
            message,
            rich_heading("❍ ɴᴏᴛ ʙʟᴏᴄᴋᴇᴅ", level=3)
            + rich_kv_table([("ᴜsᴇʀ", f"<code>{user_id}</code>")]),
        )
        return

    unblock_user(user_id)
    await rich_reply(
        message,
        rich_heading("✅ ᴜsᴇʀ ᴜɴʙʟᴏᴄᴋᴇᴅ", level=3)
        + rich_kv_table([
            ("ᴜsᴇʀ ɪᴅ", f"<code>{user_id}</code>"),
            ("ɴᴀᴍᴇ", rich_esc(user_name) if user_name else None),
        ])
        + rich_note("ᴛʜɪs ᴜsᴇʀ ᴄᴀɴ ɴᴏᴡ ᴜsᴇ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs ᴀɢᴀɪɴ."),
    )


# ── /blocklist ─────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("blocklist") & filters.user(config.OWNER_ID))
async def blocklist_cmd(_, message: Message) -> None:
    """Show all blocked groups and users."""
    groups = get_blocked_groups()
    users  = get_blocked_users()

    g_text = (
        "<br>".join(f"• <code>{g}</code>" for g in groups)
        if groups else "ɴᴏɴᴇ"
    )
    u_text = (
        "<br>".join(f"• <code>{u}</code>" for u in users)
        if users else "ɴᴏɴᴇ"
    )

    await rich_reply(
        message,
        rich_heading("🚫 ʙʟᴏᴄᴋ ʟɪsᴛ", level=3)
        + rich_note(f"<b>❍ ʙʟᴏᴄᴋᴇᴅ ɢʀᴏᴜᴘs ({len(groups)})</b><br>{g_text}")
        + rich_note(f"<b>❍ ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs ({len(users)})</b><br>{u_text}"),
    )
    

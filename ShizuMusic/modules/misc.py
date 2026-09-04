# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

"""
Utility commands:
  /repo  — send source code link
  /id    — get IDs of message / user / chat / replied message
"""

import config
from pyrogram import enums, filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from ShizuMusic import bot
from ShizuMusic.modules.block import user_allowed
from ShizuMusic.utils.rich_ui import (
    rich_details,
    rich_heading,
    rich_kv_table,
    rich_note,
    rich_reply,
)

# ── Source repo URL ────────────────────────────────────────────────────────────
SOURCE_URL = "https://github.com/Badmunda05/ShizuMusic"


# ── /repo ──────────────────────────────────────────────────────────────────────
@bot.on_message(filters.command("repo") & user_allowed)
async def repo_cmd(_, message: Message) -> None:

    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🍡 sᴏᴜʀᴄᴇ ᴄᴏᴅᴇ 🍡",
                    url=SOURCE_URL,
                    style=enums.ButtonStyle.PRIMARY,
                ),
                InlineKeyboardButton(
                    "🔱 ғᴏʀᴋ 🔱",
                    url=f"{SOURCE_URL}/fork",
                    style=enums.ButtonStyle.PRIMARY,
                ),
            ],
            [
                InlineKeyboardButton(
                    "🍬 sᴜᴘᴘᴏʀᴛ 🍬",
                    url=config.SUPPORT_GROUP,
                    style=enums.ButtonStyle.SUCCESS,
                ),
                InlineKeyboardButton(
                    "🍹 ᴜᴘᴅᴀᴛᴇs 🍹",
                    url=config.UPDATES_CHANNEL,
                    style=enums.ButtonStyle.SUCCESS,
                ),
            ],
        ]
    )

    content = (
        rich_heading("🍡 sʜɪᴢᴜᴍᴜsɪᴄ sᴏᴜʀᴄᴇ", level=3)
        + "<p>❍ ᴏᴘᴇɴ sᴏᴜʀᴄᴇ ᴍᴜsɪᴄ ʙᴏᴛ, ᴅᴇᴠᴇʟᴏᴘᴇᴅ ʙʏ <b>ʙᴀᴅ ᴍᴜɴᴅᴀ</b> ❤️</p>"
        + rich_details(
            "⚡ ʜᴏsᴛɪɴɢ sᴜᴘᴘᴏʀᴛ",
            rich_kv_table([
                ("ғʀᴇᴇ", "ʀᴇɴᴅᴇʀ ✅ · ᴋᴏʏᴇʙ ✅ · ʀᴀɪʟᴡᴀʏ ✅"),
                ("ᴘʀᴇᴍɪᴜᴍ", "ʜᴇʀᴏᴋᴜ 💎 · ᴠᴘs 🚀 (24x7 sᴍᴏᴏᴛʜ ʜᴏsᴛ)"),
            ]),
            open=True,
        )
        + rich_note(
            f"❍ <a href='{SOURCE_URL}'>ɢɪᴛʜᴜʙ ʀᴇᴘᴏ</a> — ғᴇᴇʟ ғʀᴇᴇ ᴛᴏ ʜɪᴛ ⭐ ᴏɴ ɢɪᴛʜᴜʙ!"
        )
    )

    await rich_reply(message, content, reply_markup=kb)


# ── /id ────────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("id") & user_allowed)
async def id_cmd(client, message: Message) -> None:

    chat       = message.chat
    your_id    = message.from_user.id if message.from_user else "N/A"
    message_id = message.id
    reply      = message.reply_to_message

    # ── Base rows ──────────────────────────────────────────────────────────────
    rows = [
        ("<a href='{}'>ᴍᴇssᴀɢᴇ ɪᴅ</a>".format(message.link), f"<code>{message_id}</code>"),
        (f"<a href='tg://user?id={your_id}'>ʏᴏᴜʀ ɪᴅ</a>", f"<code>{your_id}</code>"),
    ]

    # ── Optional: lookup another user by username or ID ───────────────────────
    args = message.command[1:]
    if args:
        try:
            target    = await client.get_users(args[0])
            target_id = target.id
            rows.append((f"<a href='tg://user?id={target_id}'>ᴜsᴇʀ ɪᴅ</a>", f"<code>{target_id}</code>"))
        except Exception:
            await rich_reply(
                message,
                rich_heading("❍ ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ", level=3),
            )
            return

    # ── Chat ID ────────────────────────────────────────────────────────────────
    if chat.username:
        chat_link = f"https://t.me/{chat.username}"
    else:
        chat_link = f"tg://user?id={chat.id}"

    rows.append((f"<a href='{chat_link}'>ᴄʜᴀᴛ ɪᴅ</a>", f"<code>{chat.id}</code>"))

    # ── Replied message ────────────────────────────────────────────────────────
    if reply and not getattr(reply, "empty", True):

        # Replied user ID
        if reply.from_user and not getattr(reply, "sender_chat", None):
            rows.append((f"<a href='{reply.link}'>ʀᴇᴘʟɪᴇᴅ ᴍsɢ ɪᴅ</a>", f"<code>{reply.id}</code>"))
            rows.append((
                f"<a href='tg://user?id={reply.from_user.id}'>ʀᴇᴘʟɪᴇᴅ ᴜsᴇʀ</a>",
                f"<code>{reply.from_user.id}</code>",
            ))

        # Forwarded from channel
        fwd_chat = getattr(reply, "forward_from_chat", None)
        if fwd_chat:
            rows.append(("ғᴡᴅ ᴄʜᴀɴɴᴇʟ", fwd_chat.title))
            rows.append(("ғᴡᴅ ᴄʜᴀɴɴᴇʟ ɪᴅ", f"<code>{fwd_chat.id}</code>"))

        # Sender chat (anonymous group admin / channel post)
        sender_chat = getattr(reply, "sender_chat", None)
        if sender_chat:
            rows.append(("sᴇɴᴅᴇʀ ᴄʜᴀᴛ", sender_chat.title))
            rows.append(("sᴇɴᴅᴇʀ ᴄʜᴀᴛ ɪᴅ", f"<code>{sender_chat.id}</code>"))

    content = (
        rich_heading("❍ ɪᴅ ɪɴғᴏ", level=3)
        + rich_kv_table(rows)
    )

    await rich_reply(message, content)
  

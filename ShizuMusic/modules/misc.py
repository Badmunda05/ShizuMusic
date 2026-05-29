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
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from ShizuMusic import bot
from ShizuMusic.modules.block import user_allowed

# ── Source repo URL ────────────────────────────────────────────────────────────
SOURCE_URL = "https://github.com/Badmunda05/ShizuMusic"


# ── /repo ──────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("repo") & user_allowed)
async def repo_cmd(_, message: Message) -> None:
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🍡 sᴏᴜʀᴄᴇ ᴄᴏᴅᴇ 🍡", url=SOURCE_URL),
        InlineKeyboardButton("🔱 ғᴏʀᴋ 🔱",        url=f"{SOURCE_URL}/fork"),
    ], [
        InlineKeyboardButton("🍬 sᴜᴘᴘᴏʀᴛ 🍬",  url=config.SUPPORT_GROUP),
        InlineKeyboardButton("🍹 ᴜᴘᴅᴀᴛᴇs 🍹",  url=config.UPDATES_CHANNEL),
    ]])
    await message.reply(
        "<b>╭────────────────────▣</b>\n"
        "<b>│🍡 sʜɪᴢᴜᴍᴜsɪᴄ sᴏᴜʀᴄᴇ</b>\n"
        "<b>├────────────────────▣</b>\n"
        "<b>│❍ ᴏᴘᴇɴ sᴏᴜʀᴄᴇ ᴍᴜsɪᴄ ʙᴏᴛ</b>\n"
        "<b>│❍ ᴅᴇᴠᴇʟᴏᴘᴇᴅ ʙʏ ʙᴀᴅ ᴍᴜɴᴅᴀ ❤️</b>\n"
        "<b>├────────────────────▣</b>\n"
        f"<b>│❍ <a href='{SOURCE_URL}'>ɢɪᴛʜᴜʙ ʀᴇᴘᴏ</a></b>\n"
        "<b>│❍ ғᴇᴇʟ ғʀᴇᴇ ᴛᴏ ʜɪᴛ ⭐ ᴏɴ ɢɪᴛʜᴜʙ!</b>\n"
        "<b>╰────────────────────▣</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
        disable_web_page_preview=True,
    )


# ── /id ────────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("id") & user_allowed)
async def id_cmd(client, message: Message) -> None:

    chat       = message.chat
    your_id    = message.from_user.id if message.from_user else "N/A"
    message_id = message.id
    reply      = message.reply_to_message

    # ── Base text ──────────────────────────────────────────────────────────────
    text  = f"<b>❍ <a href='{message.link}'>ᴍᴇssᴀɢᴇ ɪᴅ</a> :</b> <code>{message_id}</code>\n"
    text += f"<b>❍ <a href='tg://user?id={your_id}'>ʏᴏᴜʀ ɪᴅ</a>     :</b> <code>{your_id}</code>\n"

    # ── Optional: lookup another user by username or ID ───────────────────────
    args = message.command[1:]
    if args:
        try:
            target    = await client.get_users(args[0])
            target_id = target.id
            text += f"<b>❍ <a href='tg://user?id={target_id}'>ᴜsᴇʀ ɪᴅ</a>      :</b> <code>{target_id}</code>\n"
        except Exception:
            await message.reply(
                "<b>❍ User not found.</b>",
                parse_mode=ParseMode.HTML,
            )
            return

    # ── Chat ID ────────────────────────────────────────────────────────────────
    if chat.username:
        chat_link = f"https://t.me/{chat.username}"
    else:
        chat_link = f"tg://user?id={chat.id}"

    text += f"<b>❍ <a href='{chat_link}'>ᴄʜᴀᴛ ɪᴅ</a>      :</b> <code>{chat.id}</code>\n"

    # ── Replied message ────────────────────────────────────────────────────────
    if reply and not getattr(reply, "empty", True):

        # Replied user ID
        if reply.from_user and not getattr(reply, "sender_chat", None):
            text += (
                f"\n<b>❍ <a href='{reply.link}'>ʀᴇᴘʟɪᴇᴅ ᴍsɢ ɪᴅ</a> :</b> <code>{reply.id}</code>\n"
                f"<b>❍ <a href='tg://user?id={reply.from_user.id}'>ʀᴇᴘʟɪᴇᴅ ᴜsᴇʀ</a>    :</b> <code>{reply.from_user.id}</code>\n"
            )

        # Forwarded from channel
        if getattr(reply, "forward_from_chat", None):
            fwd = reply.forward_from_chat
            text += (
                f"\n<b>❍ ғᴡᴅ ᴄʜᴀɴɴᴇʟ    :</b> {fwd.title}\n"
                f"<b>❍ ғᴡᴅ ᴄʜᴀɴɴᴇʟ ɪᴅ :</b> <code>{fwd.id}</code>\n"
            )

        # Sender chat (anonymous group admin / channel post)
        if getattr(reply, "sender_chat", None):
            sc = reply.sender_chat
            text += (
                f"\n<b>❍ sᴇɴᴅᴇʀ ᴄʜᴀᴛ    :</b> {sc.title}\n"
                f"<b>❍ sᴇɴᴅᴇʀ ᴄʜᴀᴛ ɪᴅ :</b> <code>{sc.id}</code>\n"
            )

    await message.reply(
        text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )

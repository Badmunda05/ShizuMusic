# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import random

from pyrogram import filters
from pyrogram.errors import ChatAdminRequired
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from ShizuMusic import bot
from ShizuMusic.utils.db import (
    add_broadcast_chat,
    add_served_chat,
    remove_broadcast_chat,
    remove_served_chat,
)
from ShizuMusic.utils.rich_ui import (
    rich_esc,
    rich_heading,
    rich_img,
    rich_kv_table,
    rich_note,
    rich_send,
)

LEFT_PHOTOS = [
    "https://telegra.ph/file/1949480f01355b4e87d26.jpg",
    "https://telegra.ph/file/3ef2cc0ad2bc548bafb30.jpg",
    "https://telegra.ph/file/a7d663cd2de689b811729.jpg",
    "https://telegra.ph/file/6f19dc23847f5b005e922.jpg",
    "https://telegra.ph/file/2973150dd62fd27a3a6ba.jpg",
]


# ── Bot added to group ─────────────────────────────────────────────────────────

@bot.on_message(filters.new_chat_members, group=-10)
async def bot_added_watcher(_, message: Message) -> None:
    try:
        chat    = message.chat
        chat_id = chat.id
        me      = await bot.get_me()

        for member in message.new_chat_members:
            if member.id != me.id:
                continue

            add_served_chat(chat_id)
            add_broadcast_chat(chat_id, "group")

            added_by         = message.from_user
            added_by_mention = added_by.mention if added_by else "ᴜɴᴋɴᴏᴡɴ"

            admin_request_text = (
                rich_heading("❍ ᴛʜᴀɴᴋs ғᴏʀ ᴀᴅᴅɪɴɢ ᴍᴇ! 🥀", level=3)
                + rich_note(
                    "<p>❍ ᴘʟᴇᴀsᴇ ᴍᴀᴋᴇ ᴍᴇ ᴀɴ ᴀᴅᴍɪɴ ᴡɪᴛʜ ᴛʜᴇsᴇ ᴘᴇʀᴍɪssɪᴏɴs:</p>"
                    "<p>❍ ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇs<br>"
                    "❍ ᴍᴀɴᴀɢᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛs<br>"
                    "❍ ɪɴᴠɪᴛᴇ ᴜsᴇʀs</p>"
                )
                + rich_note("ᴡɪᴛʜᴏᴜᴛ ᴀᴅᴍɪɴ ᴘᴇʀᴍs sᴏᴍᴇ ғᴇᴀᴛᴜʀᴇs ᴡᴏɴ'ᴛ ᴡᴏʀᴋ! 🚫")
            )
            admin_kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("⚡ ᴍᴀᴋᴇ ᴍᴇ ᴀᴅᴍɪɴ ⚡", url=f"tg://user?id={me.id}")
            ]])
            try:
                await rich_send(bot, chat_id, admin_request_text, reply_markup=admin_kb)
            except Exception:
                pass

            if not config.LOGGER_ID:
                return

            try:
                invite_link = await bot.export_chat_invite_link(chat_id)
                link_text   = f"<a href='{invite_link}'>ɢᴇᴛ ʟɪɴᴋ</a>"
            except (ChatAdminRequired, Exception):
                link_text = "ɴᴏ ʟɪɴᴋ"

            try:
                count = await bot.get_chat_members_count(chat_id)
            except Exception:
                count = "N/A"

            username   = f"@{chat.username}" if chat.username else "ᴘʀɪᴠᴀᴛᴇ ɢʀᴏᴜᴘ"
            chat_photo = None
            try:
                if chat.photo:
                    chat_photo = await bot.download_media(
                        chat.photo.big_file_id,
                        file_name=f"grppp_{chat_id}.png",
                    )
            except Exception:
                chat_photo = None

            log_rows = [
                ("ᴄʜᴀᴛ ɴᴀᴍᴇ", rich_esc(chat.title)),
                ("ᴄʜᴀᴛ ɪᴅ", f"<code>{chat_id}</code>"),
                ("ᴜsᴇʀɴᴀᴍᴇ", rich_esc(username)),
                ("ɢʀᴏᴜᴘ ʟɪɴᴋ", link_text),
                ("ᴍᴇᴍʙᴇʀs", str(count)),
                ("ᴀᴅᴅᴇᴅ ʙʏ", added_by_mention),
            ]
            log_kb = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    f"👤 {added_by.first_name if added_by else 'ᴜsᴇʀ'}",
                    user_id=added_by.id if added_by else config.OWNER_ID,
                )
            ]]) if added_by else None

            try:
                if chat_photo:
                    # Locally downloaded file — no public URL, so this has
                    # to stay a caption (rich_img() only takes URLs).
                    log_text = (
                        "<b>📝 #ɴᴇᴡɢʀᴏᴜᴘ — ʙᴏᴛ ᴀᴅᴅᴇᴅ!</b>\n\n"
                        + "\n".join(f"<b>{k} :</b> {v}" for k, v in log_rows)
                    )
                    await bot.send_photo(
                        config.LOGGER_ID, photo=chat_photo,
                        caption=log_text, parse_mode=ParseMode.HTML, reply_markup=log_kb,
                    )
                else:
                    content = (
                        rich_heading("📝 #ɴᴇᴡɢʀᴏᴜᴘ — ʙᴏᴛ ᴀᴅᴅᴇᴅ!", level=3)
                        + rich_kv_table(log_rows)
                    )
                    await rich_send(bot, config.LOGGER_ID, content, reply_markup=log_kb)
            except Exception:
                pass

    except Exception as e:
        print(f"[watcher] bot_added_watcher error: {e}")


# ── Bot left / removed ─────────────────────────────────────────────────────────

@bot.on_message(filters.left_chat_member, group=-12)
async def bot_left_watcher(_, message: Message) -> None:
    try:
        left_member = message.left_chat_member
        if not left_member:
            return

        me = await bot.get_me()
        if left_member.id != me.id:
            return

        chat    = message.chat
        chat_id = chat.id

        remove_served_chat(chat_id)
        remove_broadcast_chat(chat_id)

        removed_by         = message.from_user
        removed_by_mention = removed_by.mention if removed_by else "ᴜɴᴋɴᴏᴡɴ ᴜsᴇʀ"
        username           = f"@{chat.username}" if chat.username else "ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ"

        if not config.LOGGER_ID:
            return

        content = (
            rich_heading("✫ #ʟᴇғᴛɢʀᴏᴜᴘ ✫", level=3)
            + rich_img(random.choice(LEFT_PHOTOS))
            + rich_kv_table([
                ("ᴄʜᴀᴛ ᴛɪᴛʟᴇ", rich_esc(chat.title)),
                ("ᴄʜᴀᴛ ɪᴅ", f"<code>{chat_id}</code>"),
                ("ᴜsᴇʀɴᴀᴍᴇ", rich_esc(username)),
                ("ʀᴇᴍᴏᴠᴇᴅ ʙʏ", removed_by_mention),
                ("ʙᴏᴛ", f"@{me.username}"),
            ])
        )

        try:
            await rich_send(bot, config.LOGGER_ID, content)
        except Exception:
            pass

    except Exception as e:
        print(f"[watcher] bot_left_watcher error: {e}")

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

import random

from pyrogram import filters
from pyrogram.errors import ChatAdminRequired
from pyrogram.enums import ParseMode
from pyrogram.types import Message

import config
from ShizuMusic import bot
from ShizuMusic.strings import DEFAULT_LANG, get_string
from ShizuMusic.utils.buttons import added_by_kb, make_admin_kb
from ShizuMusic.utils.db import (
    add_broadcast_chat,
    add_served_chat,
    remove_broadcast_chat,
    remove_served_chat,
)
from ShizuMusic.utils.language import chat_strings
from ShizuMusic.utils.logs import logger_active
from richgram import (
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
            en               = get_string(DEFAULT_LANG)   # log channel is the owner's: always English
            added_by_mention = added_by.mention if added_by else en["logger_unknown_user"]
            lang = chat_strings(chat_id)

            admin_request_text = (
                rich_heading("❍ " + lang["group_admin_request_title"], level=3)
                + rich_note(lang["group_admin_request_note1"])
                + rich_note(lang["group_admin_request_note2"])
            )
            admin_kb = make_admin_kb(me.id, lang=lang)
            try:
                await rich_send(bot, chat_id, admin_request_text + admin_kb)
            except Exception:
                pass

            if not logger_active():
                return

            try:
                invite_link = await bot.export_chat_invite_link(chat_id)
                link_text   = f"<a href='{invite_link}'>{en['logger_get_link']}</a>"
            except (ChatAdminRequired, Exception):
                link_text = en["logger_no_link"]

            try:
                count = await bot.get_chat_members_count(chat_id)
            except Exception:
                count = "N/A"

            username   = f"@{chat.username}" if chat.username else en["logger_private_group"]
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
                (en["kv_chat_name"], rich_esc(chat.title)),
                (en["kv_chat_id"], f"<code>{chat_id}</code>"),
                (en["kv_username"], rich_esc(username)),
                (en["kv_group_link"], link_text),
                (en["kv_members"], str(count)),
                (en["kv_added_by"], added_by_mention),
            ]
            log_kb = (
                added_by_kb(added_by.id, added_by.first_name)
                if added_by else None
            )

            try:
                if chat_photo:
                    # Locally downloaded file — no public URL, so this has
                    # to stay a caption (rich_img() only takes URLs).
                    log_text = (
                        f"<b>{en['logger_newgroup_title']}</b>\n\n"
                        + "\n".join(f"<b>{k} :</b> {v}" for k, v in log_rows)
                    )
                    await bot.send_photo(
                        config.LOGGER_ID, photo=chat_photo,
                        caption=log_text, parse_mode=ParseMode.HTML, reply_markup=log_kb,
                    )
                else:
                    content = (
                        rich_heading(en["logger_newgroup_title"], level=3)
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

        en                 = get_string(DEFAULT_LANG)   # log channel is the owner's: always English
        removed_by         = message.from_user
        removed_by_mention = removed_by.mention if removed_by else en["logger_unknown_removed_by"]
        username           = f"@{chat.username}" if chat.username else en["logger_private_chat"]

        if not logger_active():
            return

        content = (
            rich_heading(en["logger_leftgroup_title"], level=3)
            + rich_img(random.choice(LEFT_PHOTOS))
            + rich_kv_table([
                (en["kv_chat_title"], rich_esc(chat.title)),
                (en["kv_chat_id"], f"<code>{chat_id}</code>"),
                (en["kv_username"], rich_esc(username)),
                (en["kv_removed_by"], removed_by_mention),
                (en["kv_bot"], f"@{me.username}"),
            ])
        )

        try:
            await rich_send(bot, config.LOGGER_ID, content)
        except Exception:
            pass

    except Exception as e:
        print(f"[watcher] bot_left_watcher error: {e}")
        

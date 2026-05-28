# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.errors import (
    ChatAdminRequired,
    ChatWriteForbidden,
    FloodWait,
    UserIsBlocked,
)
from pyrogram.types import Message

import config
from ShizuMusic import bot


@bot.on_message(
    filters.command("broadcast")
    & filters.user(config.OWNER_ID)
)
async def broadcast_cmd(_, message: Message) -> None:

    if not message.reply_to_message:
        await message.reply(
            "<b>❍ Reply to a message</b>\n"
            "<b>❍ Then use /broadcast.</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    bm = message.reply_to_message

    # ── Load chats from DB ────────────────────────────────────────────────────
    try:
        from ShizuMusic.database import (
            get_broadcast_chats,
            get_broadcast_count,
            remove_broadcast_chat,
        )
    except Exception as e:
        await message.reply(
            f"<b>❍ DB Error:</b> <code>{e}</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    counts    = get_broadcast_count()
    all_chats = get_broadcast_chats()

    if not all_chats:
        await message.reply(
            "<b>❍ No chats found in broadcast list.</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    processing = await message.reply(
        f"<b>❍ Broadcast Started</b>\n\n"
        f"<b>❍ Total  :</b> <code>{counts['total']}</code>\n"
        f"<b>❍ Groups :</b> <code>{counts['groups']}</code>\n"
        f"<b>❍ Users  :</b> <code>{counts['private']}</code>",
        parse_mode=ParseMode.HTML,
    )

    success_g = 0   # groups
    success_u = 0   # private / users
    pinned    = 0   # successfully pinned
    failed    = 0

    for doc in all_chats:
        cid       = int(doc["chat_id"])
        chat_type = doc.get("type", "group")

        try:
            sent = await bot.forward_messages(
                cid,
                bm.chat.id,
                bm.id,
            )

            if chat_type == "group":
                success_g += 1

                # Pin in group — silently, skip if not admin
                try:
                    await bot.pin_chat_message(
                        cid,
                        sent.id,
                        disable_notification=True,
                    )
                    pinned += 1
                except ChatAdminRequired:
                    pass
                except Exception:
                    pass

            else:
                success_u += 1

        except FloodWait as e:
            await asyncio.sleep(e.value + 2)
            # Retry once after flood wait
            try:
                await bot.forward_messages(cid, bm.chat.id, bm.id)
                if chat_type == "group":
                    success_g += 1
                else:
                    success_u += 1
            except Exception:
                failed += 1

        except (UserIsBlocked, ChatWriteForbidden):
            # Bot was blocked or kicked — remove from DB
            remove_broadcast_chat(cid)
            failed += 1

        except Exception:
            failed += 1

        await asyncio.sleep(0.4)

    await processing.edit_text(
        "<b>❍ Broadcast Completed ✅</b>\n\n"
        f"<b>❍ Groups :</b> <code>{success_g}</code>\n"
        f"<b>❍ Users  :</b> <code>{success_u}</code>\n"
        f"<b>❍ Pinned :</b> <code>{pinned}</code>\n"
        f"<b>❍ Failed :</b> <code>{failed}</code>",
        parse_mode=ParseMode.HTML,
    )

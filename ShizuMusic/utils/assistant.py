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

"""
Assistant utility functions.
Handles checking whether the assistant is in a group and auto-joining it.
Previously this logic was inline in play.py — now centralised here.
"""

import asyncio

from pyrogram.errors import RPCError, UserAlreadyParticipant
from pyrogram.types import Message

from ShizuMusic import assistant, bot
from richgram import rich_edit, rich_esc, rich_heading, rich_note


async def is_assistant_in(chat_id: int):
    try:
        me     = await assistant.get_me()
        member = await assistant.get_chat_member(chat_id, me.id)
        return member.status is not None

    except Exception as e:
        err = str(e)
        if "USER_BANNED" in err or "Banned" in err:
            return "banned"
        return False


async def try_join_assistant(chat_id: int, pm: Message) -> bool:
    try:
        invite_link = await bot.export_chat_invite_link(chat_id)

    except Exception as e:
        await rich_edit(
            pm,
            rich_heading("❍ ɪ ɴᴇᴇᴅ ɪɴᴠɪᴛᴇ ʟɪɴᴋ ᴘᴇʀᴍɪssɪᴏɴ", level=3)
            + rich_note(f"<code>{rich_esc(e)}</code>"),
        )
        return False

    try:
        # Normalise joinchat link format
        if invite_link.startswith("https://t.me/+"):
            invite_link = invite_link.replace(
                "https://t.me/+",
                "https://t.me/joinchat/",
            )

        await assistant.join_chat(invite_link)
        await asyncio.sleep(2)
        return True

    except UserAlreadyParticipant:
        return True

    except RPCError as e:
        await rich_edit(
            pm,
            rich_heading("❍ ᴀssɪsᴛᴀɴᴛ ᴊᴏɪɴ ғᴀɪʟᴇᴅ", level=3)
            + rich_note(f"<code>{rich_esc(e)}</code>"),
        )
        return False

    except Exception as e:
        await rich_edit(
            pm,
            rich_heading("❍ ᴊᴏɪɴ ᴇʀʀᴏʀ", level=3)
            + rich_note(f"<code>{rich_esc(e)}</code>"),
        )
        return False
        

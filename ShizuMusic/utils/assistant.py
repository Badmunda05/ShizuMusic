# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

"""
Assistant utility functions.
Handles checking whether the assistant is in a group and auto-joining it.
Previously this logic was inline in play.py — now centralised here.
"""

import asyncio

from pyrogram.errors import RPCError, UserAlreadyParticipant
from pyrogram.types import Message

from ShizuMusic import assistant, bot
from ShizuMusic.utils.rich_ui import rich_edit, rich_esc, rich_heading, rich_note


async def is_assistant_in(chat_id: int):
    """
    Check whether the assistant is a member of the given group.

    Returns:
        True     — assistant is present
        False    — assistant is not present
        "banned" — assistant was banned from the group
    """
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
    """
    Attempt to make the assistant join the group via invite link.

    Args:
        chat_id: Target group chat ID.
        pm:      Status message to edit with progress / error text.

    Returns:
        True on success, False on failure.
    """
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
        

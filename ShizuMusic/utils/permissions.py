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

from typing import Union

from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.types import CallbackQuery, Message

import config

TRUSTED_IDS: set[int] = {777000, config.OWNER_ID}


async def is_user_authorized(obj: Union[Message, CallbackQuery]) -> bool:
    """
    Returns True if the user is:
    - Bot owner or Telegram system account (777000)
    - A group admin or owner
    """
    if isinstance(obj, CallbackQuery):
        message = obj.message
        user    = obj.from_user
    elif isinstance(obj, Message):
        message = obj
        user    = obj.from_user
    else:
        return False

    if not user:
        return False

    if user.id in TRUSTED_IDS:
        return True

    if message.chat.type not in (ChatType.SUPERGROUP, ChatType.GROUP, ChatType.CHANNEL):
        return False

    try:
        member = await message._client.get_chat_member(message.chat.id, user.id)
        return member.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)
    except Exception:
        return False

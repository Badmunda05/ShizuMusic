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

from pyrogram import filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from ShizuMusic import bot


async def _block_middleware(_, message: Message) -> None:
    try:
        # Import from utils.db directly — no circular dependency
        from ShizuMusic.utils.db import is_group_blocked, is_user_blocked_db
    except ImportError:
        return

    chat_id = message.chat.id      if message.chat      else None
    user_id = message.from_user.id if message.from_user else None

    if chat_id and is_group_blocked(chat_id):
        message.stop_propagation()
        return

    if user_id and is_user_blocked_db(user_id):
        message.stop_propagation()
        return


def register_block_middleware() -> None:
    bot.add_handler(
        MessageHandler(
            _block_middleware,
            filters=filters.all,
        ),
        group=-1,
    )
    

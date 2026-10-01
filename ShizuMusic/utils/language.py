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

from ShizuMusic.strings import DEFAULT_LANG, get_string
from ShizuMusic.utils.db import get_chat_lang
from ShizuMusic.utils.routes import notify_chat


def chat_strings(chat_id: int) -> dict:
    """This chat's chosen language strings (falls back to English)."""
    try:
        lang = get_chat_lang(notify_chat(chat_id))   # channel VC -> its group's language
    except Exception:
        lang = DEFAULT_LANG
    return get_string(lang)

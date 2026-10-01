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

from ShizuMusic.utils.db import (
    start_mongo,
    get_db,
    is_connected,
    get_mongo_client,
    add_served_chat,
    get_served_chats,
    get_served_chats_count,
    remove_served_chat,
    add_served_user,
    get_served_users,
    get_served_users_count,
    ban_chat,
    unban_chat,
    is_chat_banned,
    get_banned_chats,
    get_banned_chats_count,
    mark_assistant_joined,
    is_assistant_joined,
    increment_play_count,
    get_total_plays,
    add_broadcast_chat,
    get_broadcast_chats,
    get_broadcast_count,
    remove_broadcast_chat,
    is_group_blocked,
    block_group,
    unblock_group,
    get_blocked_groups,
    is_user_blocked_db,
    block_user,
    unblock_user,
    get_blocked_users,
    save_chat_effects,
    load_chat_effects,
    delete_chat_effects,
    is_autoplay_enabled,
    set_autoplay_enabled,
    get_autoplay_lang,
    set_autoplay_lang,
    get_autoplay_mood,
    set_autoplay_mood,
    get_chat_lang,
    set_chat_lang,
    is_thumbnail_enabled,
    set_thumbnail_enabled,
)

__all__ = [
    "start_mongo", "get_db", "is_connected", "get_mongo_client",
    "add_served_chat", "get_served_chats", "get_served_chats_count", "remove_served_chat",
    "add_served_user", "get_served_users", "get_served_users_count",
    "ban_chat", "unban_chat", "is_chat_banned", "get_banned_chats", "get_banned_chats_count",
    "mark_assistant_joined", "is_assistant_joined",
    "increment_play_count", "get_total_plays",
    "add_broadcast_chat", "get_broadcast_chats", "get_broadcast_count", "remove_broadcast_chat",
    "is_group_blocked", "block_group", "unblock_group", "get_blocked_groups",
    "is_user_blocked_db", "block_user", "unblock_user", "get_blocked_users",
    "save_chat_effects", "load_chat_effects", "delete_chat_effects",
    "is_autoplay_enabled", "set_autoplay_enabled",
    "get_autoplay_lang", "set_autoplay_lang",
    "get_autoplay_mood", "set_autoplay_mood",
    "get_chat_lang", "set_chat_lang",
    "is_thumbnail_enabled", "set_thumbnail_enabled",
]

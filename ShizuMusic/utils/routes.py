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

route: dict[int, int] = {}              # channel id -> group id
group_channel: dict[int, int] = {}      # group id   -> channel id
_panel_vc: dict[tuple[int, int], int] = {}   # (chat, message id) -> vc id


def register_link(group_id: int, channel_id: int) -> None:
    old = group_channel.get(group_id)
    if old is not None and old != channel_id:
        route.pop(old, None)
    group_channel[group_id] = channel_id
    route[channel_id] = group_id


def unregister_group(group_id: int) -> None:
    channel_id = group_channel.pop(group_id, None)
    if channel_id is not None:
        route.pop(channel_id, None)


def notify_chat(chat_id: int) -> int:
    """Where messages about `chat_id` should be written (group for a channel)."""
    return route.get(chat_id, chat_id)


def register_panel(chat_id: int, message_id: int, vc_id: int) -> None:
    """Remember which VC a player panel controls (only needed for channels)."""
    if chat_id == vc_id:
        return
    if len(_panel_vc) > 1000:
        for k in list(_panel_vc)[:200]:
            _panel_vc.pop(k, None)
    _panel_vc[(chat_id, message_id)] = vc_id


def panel_target(chat_id: int, message_id: int) -> int:
    """VC id a button press on this panel message should act on."""
    return _panel_vc.get((chat_id, message_id), chat_id)

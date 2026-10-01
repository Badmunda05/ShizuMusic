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
import re

from ShizuMusic import LOGGER, bot
from ShizuMusic.utils.db import get_all_channel_links
from ShizuMusic.utils.language import chat_strings
from richgram import rich_heading, rich_note, rich_send
from ShizuMusic.utils.routes import group_channel, register_link, route

# every command that means "same as the normal one, but for the channel"
CHANNEL_CMDS = {
    "cplay", "cvplay", "cplayforce", "cvplayforce", "cpplay",
    "cpause", "cresume", "cskip", "cstop", "cend", "cclear",
    "cseek", "cseekback",
    "cspeed", "cspeedreset", "cbass", "cbassoff",
    "ceffecton", "ceffectoff", "ceffects",
    "cautoplay", "cthumbnail",
}

_CMD_RE = re.compile(r"^/(\w+)")


async def target_chat(message):
    """
    Chat id whose voice chat / queue this command controls.
    Returns None (after replying) when a c-command is used in a group that
    has no channel linked.
    """
    group_id = message.chat.id
    text = message.text or message.caption or ""
    m = _CMD_RE.match(text)
    name = m.group(1).lower() if m else ""

    if name not in CHANNEL_CMDS:
        return group_id

    channel_id = group_channel.get(group_id)
    if channel_id is None:
        lang = chat_strings(group_id)
        await rich_send(
            bot, group_id,
            rich_heading(lang["ch_not_linked_title"], level=3)
            + rich_note(lang["ch_not_linked_note"]),
        )
        return None

    register_link(group_id, channel_id)     # keep the reverse route fresh
    return channel_id


def load_links() -> None:
    for group_id, channel_id in get_all_channel_links().items():
        register_link(group_id, channel_id)
    LOGGER.info(f"[Channels] {len(route)} linked channel(s) loaded")


def install_redirect() -> None:
    """Deliver bot messages addressed to a linked channel to its group."""
    if getattr(bot, "_channel_redirect_installed", False):
        return

    for name in ("send_rich_message", "send_message"):
        orig = getattr(bot, name, None)
        if orig is None:
            continue

        async def wrapper(*args, _orig=orig, **kwargs):
            cid = kwargs.get("chat_id")
            if cid is not None and cid in route:
                kwargs["chat_id"] = route[cid]
            elif args and isinstance(args[0], int) and args[0] in route:
                args = (route[args[0]],) + args[1:]
            return await _orig(*args, **kwargs)

        setattr(bot, name, wrapper)

    bot._channel_redirect_installed = True


load_links()
install_redirect()

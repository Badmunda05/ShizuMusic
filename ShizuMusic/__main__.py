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

import asyncio
import importlib
import os
import re
import sys
import threading
import time

import requests
from flask import Flask
from pyrogram import idle
from pyrogram.types import BotCommand

import config
from ShizuMusic import LOGGER, assistant, bot, call_py
from ShizuMusic.modules import ALL_MODULES
from ShizuMusic.utils.logs import logger_active
from richgram import (
    rich_esc,
    rich_heading,
    rich_kv_table,
    rich_send,
)

ASSISTANT_USERNAME: str = ""

# ── Flask health check ────────────────────────────────────────────────────────

_flask = Flask(__name__)


@_flask.route("/")
def _home():
    return "❍ ꜱʜɪᴢᴜᴍᴜꜱɪᴄ ɪꜱ ʀᴜɴɴɪɴɢ ᴍᴀᴅᴇ ʙʏ ʙᴀᴅᴍᴜɴᴅᴀ 💕", 200


@_flask.route("/health")
def _health():
    return "OK", 200


def _run_flask() -> None:
    _flask.run(host="0.0.0.0", port=config.PORT, use_reloader=False)


# ── Keep-Alive ────────────────────────────────────────────────────────────────

def _keep_alive() -> None:
    url = os.getenv("RENDER_EXTERNAL_URL", f"http://0.0.0.0:{config.PORT}")
    while True:
        try:
            requests.get(url, timeout=10)
            LOGGER.info(f"Keep-alive ping sent → {url}")
        except Exception as e:
            LOGGER.warning(f"Keep-alive ping failed: {e}")
        time.sleep(300)


# ── Startup notification ──────────────────────────────────────────────────────


async def _notify_owner(me, assistant_username: str) -> None:
    if not logger_active():
        return

    try:
        content = (
            rich_heading(
                "🎵 ꜱʜɪᴢᴜᴍᴜꜱɪᴄ ꜱᴛᴀʀᴛᴇᴅ 💕",
                level=3
            )
            + rich_kv_table([
                (
                    "ʙᴏᴛ",
                    f"@{rich_esc(me.username or 'N/A')}"
                ),
                (
                    "ᴀꜱꜱɪꜱᴛᴀɴᴛ",
                    f"@{rich_esc(assistant_username)}"
                ),
            ])
        )

        await rich_send(
            bot,
            config.LOGGER_ID,
            content,
        )

    except Exception as e:
        LOGGER.warning(
            f"Logger Notification Error : {e}"
        )

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # 1. MongoDB
    try:
        from ShizuMusic.utils.db import start_mongo
        ok = start_mongo()
        if ok:
            LOGGER.info("MongoDB ready.")
        else:
            LOGGER.warning("MongoDB not connected — continuing without DB.")
    except Exception as e:
        LOGGER.warning(f"MongoDB startup error: {e} — continuing without DB.")

    # 2. Flask
    threading.Thread(target=_run_flask, daemon=True).start()
    LOGGER.info(f"Flask health server on port {config.PORT}")

    # 3. Keep-alive ping
    threading.Thread(target=_keep_alive, daemon=True).start()
    LOGGER.info("Keep-alive thread started")

    # 4. Bot start
    for attempt in range(10):
        try:
            bot.start()
            LOGGER.info("Bot client started")
            break
        except Exception as e:
            if "FLOOD_WAIT" in str(e):
                m    = re.search(r"(\d+)", str(e))
                wait = min(int(m.group(1)) + 5 if m else 300, 1800)
                LOGGER.warning(f"FLOOD_WAIT — sleeping {wait}s (attempt {attempt + 1}/10)")
                time.sleep(wait)
            else:
                LOGGER.error(f"Bot start failed: {e}")
                sys.exit(1)
    else:
        LOGGER.error("Bot failed to start after 10 attempts")
        sys.exit(1)

    me = bot.get_me()
    LOGGER.info(f"Bot: @{me.username}")
    import ShizuMusic
    from pytgcalls import PyTgCalls
    ShizuMusic.call_py = PyTgCalls(assistant)
    call_py = ShizuMusic.call_py

    # 5. Set bot commands
    try:
        bot.set_bot_commands([
            BotCommand("start",  "✧ sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ✧"),
            BotCommand("help",   "✧ ɢᴇᴛ ʜᴇʟᴘ ᴍᴇɴᴜ ✧"),
            BotCommand("play",   "✧ ᴘʟᴀʏ ᴀ sᴏɴɢ ✧"),
            BotCommand("pause",  "✧ ᴘᴀᴜsᴇ ᴘʟᴀʏʙᴀᴄᴋ ✧"),
            BotCommand("resume", "✧ ʀᴇsᴜᴍᴇ ᴘʟᴀʏʙᴀᴄᴋ ✧"),
            BotCommand("skip",   "✧ sᴋɪᴘ sᴏɴɢ ✧"),
            BotCommand("stop",   "✧ sᴛᴏᴘ & ᴄʟᴇᴀʀ ✧"),
            BotCommand("ping",   "✧ ʙᴏᴛ sᴛᴀᴛs ✧"),
            BotCommand("autoplay", "✧ ᴀᴜᴛᴏ-ᴘʟᴀʏ ʀᴇʟᴀᴛᴇᴅ sᴏɴɢs ✧"),
            BotCommand("language", "✧ ᴄʜᴀɴɢᴇ ʙᴏᴛ ʟᴀɴɢᴜᴀɢᴇ ✧"),
            BotCommand("playforce", "✧ ᴘʟᴀʏ ɴᴏᴡ, ᴋᴇᴇᴘ ǫᴜᴇᴜᴇ ✧"),
            BotCommand("pcreate", "✧ ᴄʀᴇᴀᴛᴇ ᴀ ᴘʟᴀʏʟɪsᴛ ✧"),
            BotCommand("padd", "✧ ᴀᴅᴅ sᴏɴɢ ᴛᴏ ᴘʟᴀʏʟɪsᴛ ✧"),
            BotCommand("premove", "✧ ʀᴇᴍᴏᴠᴇ sᴏɴɢ ғʀᴏᴍ ᴘʟᴀʏʟɪsᴛ ✧"),
            BotCommand("pview", "✧ ᴠɪᴇᴡ ᴘʟᴀʏʟɪsᴛs ✧"),
            BotCommand("pplay", "✧ ᴘʟᴀʏ ᴀ ᴘʟᴀʏʟɪsᴛ ✧"),
            BotCommand("pdelete", "✧ ᴅᴇʟᴇᴛᴇ ᴀ ᴘʟᴀʏʟɪsᴛ ✧"),
            BotCommand("addchannel", "✧ ʟɪɴᴋ ᴀ ᴄʜᴀɴɴᴇʟ ғᴏʀ ᴘʟᴀʏ ✧"),
            BotCommand("delchannel", "✧ ᴜɴʟɪɴᴋ ᴄʜᴀɴɴᴇʟ ✧"),
            BotCommand("cplay", "✧ ᴘʟᴀʏ ɪɴ ᴄʜᴀɴɴᴇʟ ✧"),
            BotCommand("cvplay", "✧ ᴠɪᴅᴇᴏ ɪɴ ᴄʜᴀɴɴᴇʟ ✧"),
            BotCommand("cpause", "✧ ᴘᴀᴜsᴇ ᴄʜᴀɴɴᴇʟ ✧"),
            BotCommand("cresume", "✧ ʀᴇsᴜᴍᴇ ᴄʜᴀɴɴᴇʟ ✧"),
            BotCommand("cskip", "✧ sᴋɪᴘ ɪɴ ᴄʜᴀɴɴᴇʟ ✧"),
            BotCommand("cstop", "✧ sᴛᴏᴘ ᴄʜᴀɴɴᴇʟ ✧"),
            BotCommand("thumbnail", "✧ sᴏɴɢ ᴛʜᴜᴍʙɴᴀɪʟ ᴏɴ/ᴏғғ ✧"),
            BotCommand("repo",   "✧ sᴏᴜʀᴄᴇ ᴍᴜsɪᴄ ʙᴏᴛ ✧"),
        ])
        LOGGER.info("Bot commands set")
    except Exception as e:
        LOGGER.warning(f"Could not set bot commands: {e}")

    # 6. Assistant — started
    try:
        if not assistant.is_connected:
            assistant.start()
        am = assistant.get_me()
        ASSISTANT_USERNAME = am.username or ""
        LOGGER.info(f"Assistant: @{ASSISTANT_USERNAME}")
    except Exception as e:
        LOGGER.error(f"Assistant start failed: {e}")
        sys.exit(1)

    # 7. PyTgCalls
    call_py.start()
    LOGGER.info("PyTgCalls started")

    # 8. Block middleware
    try:
        from ShizuMusic.utils.decorators import register_block_middleware
        register_block_middleware()
        LOGGER.info("Block middleware registered")
    except Exception as e:
        LOGGER.warning(f"Block middleware load failed: {e}")

    # 9. Load modules
    for mod in ALL_MODULES:
        try:
            importlib.import_module(f"ShizuMusic.modules.{mod}")
            LOGGER.info(f"Loaded module: {mod}")
        except Exception as e:
            LOGGER.error(f"Failed to load module {mod}: {e}")

    # 10. Stream-end handler
    try:
        import ShizuMusic.core.call  # noqa: F401
    except Exception as e:
        LOGGER.error(f"Failed to load call handler: {e}")

    # 11. Notify owner
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_notify_owner(me, ASSISTANT_USERNAME))

    # 12. Watchdog
    from ShizuMusic.core.watcher import watchdog
    loop.create_task(watchdog())
    LOGGER.info("Watchdog started")

    LOGGER.info("ShizuMusic is running")

    idle()

    # ── Graceful shutdown ─────────────────────────────────────────────────────
    try:
        bot.stop()
    except Exception:
        pass

    try:
        assistant.stop()
    except Exception:
        pass

    LOGGER.info("✧ ShizuMusic stopped ✧")

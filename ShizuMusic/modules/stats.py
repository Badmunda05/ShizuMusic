# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import platform
import sys

import psutil
from pyrogram import filters
from pyrogram.types import Message

import config
from ShizuMusic import bot
from ShizuMusic.utils.db import (
    get_mongo_client,
    get_served_chats_count,
    get_served_users_count,
    get_banned_chats_count,
    get_total_plays,
    get_broadcast_count,
    is_connected,
)
from ShizuMusic.utils.rich_ui import (
    rich_edit,
    rich_esc,
    rich_heading,
    rich_kv_table,
    rich_reply,
)


@bot.on_message(
    filters.command("stats")
    & filters.user(config.OWNER_ID)
)
async def stats_cmd(_, message: Message) -> None:
    """Full system + MongoDB stats for the bot owner."""

    processing = await rich_reply(
        message,
        rich_heading("❍ ғᴇᴛᴄʜɪɴɢ sᴛᴀᴛs...", level=3),
    )

    # ── System stats ──────────────────────────────────────────────────────────
    try:
        cpu_percent  = psutil.cpu_percent(interval=1)
        cpu_freq     = psutil.cpu_freq()
        freq_str     = f"{cpu_freq.current:.0f} MHz" if cpu_freq else "N/A"
        p_cores      = psutil.cpu_count(logical=False) or "N/A"
        t_cores      = psutil.cpu_count(logical=True)  or "N/A"

        ram          = psutil.virtual_memory()
        ram_total    = ram.total     / (1024 ** 3)
        ram_used     = ram.used      / (1024 ** 3)
        ram_free     = ram.available / (1024 ** 3)
        ram_percent  = ram.percent

        hdd          = psutil.disk_usage("/")
        disk_total   = hdd.total / (1024 ** 3)
        disk_used    = hdd.used  / (1024 ** 3)
        disk_free    = hdd.free  / (1024 ** 3)
        disk_percent = hdd.percent

        py_version   = sys.version.split()[0]
        os_name      = platform.system()
        os_release   = platform.release()

    except Exception as e:
        err_text = rich_heading("❍ sʏsᴛᴇᴍ sᴛᴀᴛs ᴇʀʀᴏʀ", level=3) + f"<p><code>{rich_esc(e)}</code></p>"
        if processing is not None:
            await rich_edit(processing, err_text)
        else:
            await rich_reply(message, err_text)
        return

    # ── MongoDB stats ─────────────────────────────────────────────────────────
    db_rows = [("ᴍᴏɴɢᴏᴅʙ", "<code>ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ</code>")]
    if is_connected():
        try:
            client   = get_mongo_client()
            db_stats = client["ShizuMusic"].command("dbstats")
            data_kb  = db_stats.get("dataSize",    0) / 1024
            stor_kb  = db_stats.get("storageSize", 0) / 1024
            col_cnt  = db_stats.get("collections", 0)
            obj_cnt  = db_stats.get("objects",     0)
            db_rows  = [
                ("ᴅʙ ᴅᴀᴛᴀ", f"<code>{data_kb:.2f} KB</code>"),
                ("ᴅʙ sᴛᴏʀᴀɢᴇ", f"<code>{stor_kb:.2f} KB</code>"),
                ("ᴄᴏʟʟᴇᴄᴛɪᴏɴs", f"<code>{col_cnt}</code>"),
                ("ᴏʙᴊᴇᴄᴛs", f"<code>{obj_cnt}</code>"),
            ]
        except Exception as e:
            db_rows = [("ᴍᴏɴɢᴏᴅʙ ᴇʀʀᴏʀ", f"<code>{rich_esc(e)}</code>")]

    # ── Bot DB counts ─────────────────────────────────────────────────────────
    served_chats = get_served_chats_count()
    served_users = get_served_users_count()
    banned_chats = get_banned_chats_count()
    total_plays  = get_total_plays()
    bc           = get_broadcast_count()

    # ── Final message ─────────────────────────────────────────────────────────
    text = (
        rich_heading("📊 sʜɪᴢᴜᴍᴜsɪᴄ sᴛᴀᴛs", level=2)

        + rich_heading("❍ sʏsᴛᴇᴍ", level=4)
        + rich_kv_table([
            ("ᴏs", f"<code>{rich_esc(os_name)} {rich_esc(os_release)}</code>"),
            ("ᴘʏᴛʜᴏɴ", f"<code>{rich_esc(py_version)}</code>"),
            ("ᴄᴘᴜ ᴜsᴀɢᴇ", f"<code>{cpu_percent}%</code>"),
            ("ᴄᴘᴜ ғʀᴇǫ", f"<code>{freq_str}</code>"),
            ("ᴘ-ᴄᴏʀᴇs", f"<code>{p_cores}</code>"),
            ("ᴛ-ᴄᴏʀᴇs", f"<code>{t_cores}</code>"),
        ])

        + rich_heading("❍ ᴍᴇᴍᴏʀʏ (ʀᴀᴍ)", level=4)
        + rich_kv_table([
            ("ᴛᴏᴛᴀʟ", f"<code>{ram_total:.2f} GB</code>"),
            ("ᴜsᴇᴅ", f"<code>{ram_used:.2f} GB ({ram_percent}%)</code>"),
            ("ғʀᴇᴇ", f"<code>{ram_free:.2f} GB</code>"),
        ])

        + rich_heading("❍ ᴅɪsᴋ", level=4)
        + rich_kv_table([
            ("ᴛᴏᴛᴀʟ", f"<code>{disk_total:.2f} GB</code>"),
            ("ᴜsᴇᴅ", f"<code>{disk_used:.2f} GB ({disk_percent}%)</code>"),
            ("ғʀᴇᴇ", f"<code>{disk_free:.2f} GB</code>"),
        ])

        + rich_heading("❍ ᴍᴏɴɢᴏᴅʙ", level=4)
        + rich_kv_table(db_rows)

        + rich_heading("❍ ʙᴏᴛ sᴛᴀᴛs", level=4)
        + rich_kv_table([
            ("sᴇʀᴠᴇᴅ ᴄʜᴀᴛs", f"<code>{served_chats}</code>"),
            ("sᴇʀᴠᴇᴅ ᴜsᴇʀs", f"<code>{served_users}</code>"),
            ("ʙᴀɴɴᴇᴅ ᴄʜᴀᴛs", f"<code>{banned_chats}</code>"),
            ("ᴛᴏᴛᴀʟ ᴘʟᴀʏs", f"<code>{total_plays}</code>"),
        ])

        + rich_heading("❍ ʙʀᴏᴀᴅᴄᴀsᴛ ʟɪsᴛ", level=4)
        + rich_kv_table([
            ("ᴛᴏᴛᴀʟ", f"<code>{bc['total']}</code>"),
            ("ɢʀᴏᴜᴘs", f"<code>{bc['groups']}</code>"),
            ("ᴜsᴇʀs", f"<code>{bc['private']}</code>"),
        ])
    )

    if processing is not None:
        await rich_edit(processing, text)
    else:
        await rich_reply(message, text)
        

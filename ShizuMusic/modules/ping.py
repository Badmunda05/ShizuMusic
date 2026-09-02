# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio
import os
import time
from datetime import timedelta

import psutil
import speedtest
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from ShizuMusic import bot, assistant, bot_start_time
from ShizuMusic.modules.block import user_allowed
from ShizuMusic.utils.rich_ui import (
    rich_caption,
    rich_esc,
    rich_heading,
    rich_kv_table,
    rich_send,
)


def supp_markup():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(text="🍬 sᴜᴘᴘᴏʀᴛ 🍬", url=config.SUPPORT_GROUP),
    ]])


# ── /ping ──────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("ping") & user_allowed)
async def ping_cmd(client, message: Message) -> None:

    chat_id = message.chat.id
    start   = time.perf_counter()
    pm      = await rich_send(
        bot, chat_id,
        rich_heading(f"❍ {rich_esc(client.me.first_name)} ɪs ᴘɪɴɢɪɴɢ...", level=3),
    )
    latency = round((time.perf_counter() - start) * 1000)
    uptime  = str(timedelta(seconds=int(time.time() - bot_start_time)))
    cpu     = psutil.cpu_percent(interval=1)

    process = psutil.Process(os.getpid())
    ram     = process.memory_info().rss / 1024 / 1024

    disk    = psutil.disk_usage("/")
    disk_str = (
        f"{disk.used // (1024**3)}GB / "
        f"{disk.total // (1024**3)}GB "
        f"({disk.percent}%)"
    )

    try:
        pytg_start = time.perf_counter()
        await assistant.get_me()
        pytg = round((time.perf_counter() - pytg_start) * 1000)
    except Exception:
        pytg = "N/A"

    try:
        await pm.delete()
    except Exception:
        pass

    caption = (
        rich_heading(f"🏓 ᴘᴏɴɢ : {latency}ms", level=3)
        + rich_kv_table([
            ("ᴜᴘᴛɪᴍᴇ", f"<code>{uptime}</code>"),
            ("ʀᴀᴍ", f"<code>{ram:.2f} MB</code>"),
            ("ᴄᴘᴜ", f"<code>{cpu}%</code>"),
            ("ᴅɪsᴋ", f"<code>{disk_str}</code>"),
            ("ᴘʏᴛɢᴄ", f"<code>{pytg}ms</code>"),
        ])
        + f"<p>❍ ʙʏ » <a href=\"{config.SUPPORT_GROUP}\">sʜɪᴢᴜ-ᴍᴜsɪᴄ™</a></p>"
    )

    await message.reply_photo(
        photo=config.PING_IMG_URL,
        caption=rich_caption(caption),
        parse_mode=ParseMode.HTML,
        reply_markup=supp_markup(),
    )


# ── /speedtest ─────────────────────────────────────────────────────────────────

def _run_speedtest(m):
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        st.download()
        st.upload()
        st.results.share()
        return st.results.dict()
    except Exception:
        return None


@bot.on_message(
    filters.command(["speedtest", "spt"])
    & filters.user(config.OWNER_ID)
)
async def speedtest_cmd(client, message: Message) -> None:

    chat_id = message.chat.id
    m = await rich_send(bot, chat_id, rich_heading("❍ sᴛᴀʀᴛɪɴɢ sᴘᴇᴇᴅ ᴛᴇsᴛ, ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...", level=3))

    loop   = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _run_speedtest, m)

    if result is None:
        from ShizuMusic.utils.rich_ui import rich_edit
        await rich_edit(m, rich_heading("❍ sᴘᴇᴇᴅᴛᴇsᴛ ғᴀɪʟᴇᴅ, ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ", level=3))
        return

    download = result["download"] / 1_000_000
    upload   = result["upload"]   / 1_000_000
    ping     = result["ping"]
    isp      = result["client"]["isp"]
    country  = result["client"]["country"]
    server   = result["server"]["name"]
    sponsor  = result["server"]["sponsor"]
    s_cc     = result["server"]["cc"]
    s_lat    = result["server"]["latency"]
    share    = result["share"]

    caption = (
        rich_heading("⚡ sᴘᴇᴇᴅᴛᴇsᴛ ʀᴇsᴜʟᴛs", level=3)
        + rich_kv_table([
            ("ɪsᴘ", f"<code>{rich_esc(isp)}</code>"),
            ("ᴄᴏᴜɴᴛʀʏ", f"<code>{rich_esc(country)}</code>"),
        ], headers=["ᴄʟɪᴇɴᴛ ɪɴғᴏ", ""])
        + rich_kv_table([
            ("ɴᴀᴍᴇ", f"<code>{rich_esc(server)}</code>"),
            ("sᴘᴏɴsᴏʀ", f"<code>{rich_esc(sponsor)}</code>"),
            ("ᴄᴏᴜɴᴛʀʏ", f"<code>{rich_esc(s_cc)}</code>"),
            ("ʟᴀᴛᴇɴᴄʏ", f"<code>{s_lat} ms</code>"),
        ], headers=["sᴇʀᴠᴇʀ ɪɴғᴏ", ""])
        + rich_kv_table([
            ("ᴘɪɴɢ", f"<code>{ping:.2f} ms</code>"),
            ("ᴅᴏᴡɴʟᴏᴀᴅ", f"<code>{download:.2f} Mbps</code>"),
            ("ᴜᴘʟᴏᴀᴅ", f"<code>{upload:.2f} Mbps</code>"),
        ], headers=["sᴘᴇᴇᴅ", ""])
        + f"<p>❍ ʙʏ » <a href=\"{config.SUPPORT_GROUP}\">sʜɪᴢᴜ-ᴍᴜsɪᴄ™</a></p>"
    )

    try:
        await m.delete()
    except Exception:
        pass
    await message.reply_photo(
        photo=share,
        caption=rich_caption(caption),
        parse_mode=ParseMode.HTML,
        reply_markup=supp_markup(),
    )
    

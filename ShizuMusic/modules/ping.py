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

def supp_markup():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="🍬 sᴜᴘᴘᴏʀᴛ 🍬",
                    url=config.SUPPORT_GROUP,
                ),
            ]
        ]
    )


# ══════════════════════════════════════════════════════════════════════════════
# /ping
# ══════════════════════════════════════════════════════════════════════════════

@bot.on_message(filters.command("ping"))
async def ping_cmd(client, message: Message) -> None:

    # Ping Start
    start = time.perf_counter()

    pm = await message.reply_text(
        f"<b>❍ {client.me.first_name} ɪs ᴘɪɴɢɪɴɢ...</b>",
        parse_mode=ParseMode.HTML,
    )

    latency = round((time.perf_counter() - start) * 1000)

    # Uptime
    uptime = str(timedelta(seconds=int(time.time() - bot_start_time)))

    # CPU Usage
    cpu = psutil.cpu_percent(interval=1)

    # BOT RAM Usage
    process = psutil.Process(os.getpid())
    ram = process.memory_info().rss / 1024 / 1024
    ram_str = f"{ram:.2f} MB"

    # Disk Usage
    disk = psutil.disk_usage("/")
    disk_str = (
        f"{disk.used // (1024**3)}GB / "
        f"{disk.total // (1024**3)}GB "
        f"({disk.percent}%)"
    )

    # Assistant Ping
    try:
        pytg_start = time.perf_counter()
        await assistant.get_me()
        pytg = round((time.perf_counter() - pytg_start) * 1000)
    except Exception:
        pytg = "N/A"

    await pm.delete()

    caption = f"""
<b>🏓 ᴘᴏɴɢ : <code>{latency}ms</code></b>

<b><u>{client.me.first_name} sʏsᴛᴇᴍ sᴛᴀᴛs :</u></b>

<b>❍ ᴜᴘᴛɪᴍᴇ :</b> <code>{uptime}</code>
<b>❍ ʀᴀᴍ :</b> <code>{ram_str}</code>
<b>❍ ᴄᴘᴜ :</b> <code>{cpu}%</code>
<b>❍ ᴅɪsᴋ :</b> <code>{disk_str}</code>
<b>❍ ᴘʏᴛɢᴄ :</b> <code>{pytg}ms</code>

<b>❍ 𝖡ʏ » <a href="{config.SUPPORT_GROUP}">Aʟᴘʜᴀ_Mᴜsɪᴄ™</a></b>
"""

    await message.reply_photo(
        photo=config.PING_IMG_URL,
        caption=caption,
        parse_mode=ParseMode.HTML,
        reply_markup=supp_markup(),
    )


# ══════════════════════════════════════════════════════════════════════════════
# /speedtest  (sudo only)
# ══════════════════════════════════════════════════════════════════════════════

def _run_speedtest(m):
    """Blocking speedtest — runs in executor so it won't freeze the bot."""
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        m = m.edit_text("<b>❍ ᴛᴇsᴛɪɴɢ ᴅᴏᴡɴʟᴏᴀᴅ sᴘᴇᴇᴅ...</b>")
        st.download()
        m = m.edit_text("<b>❍ ᴛᴇsᴛɪɴɢ ᴜᴘʟᴏᴀᴅ sᴘᴇᴇᴅ...</b>")
        st.upload()
        st.results.share()
        return st.results.dict()
    except Exception as e:
        m.edit_text(f"<b>❍ ᴇʀʀᴏʀ :</b> <code>{e}</code>")
        return None


@bot.on_message(filters.command(["speedtest", "spt"]) & filters.user(config.OWNER_ID))
async def speedtest_cmd(client, message: Message) -> None:

    m = await message.reply_text(
        "<b>❍ sᴛᴀʀᴛɪɴɢ sᴘᴇᴇᴅ ᴛᴇsᴛ, ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>",
        parse_mode=ParseMode.HTML,
    )

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _run_speedtest, m)

    if result is None:
        return  # error already shown inside _run_speedtest

    # ── Parse results ─────────────────────────────────────────────────────────
    download = result["download"] / 1_000_000        # Mbps
    upload   = result["upload"]   / 1_000_000        # Mbps
    ping     = result["ping"]
    isp      = result["client"]["isp"]
    country  = result["client"]["country"]
    server   = result["server"]["name"]
    sponsor  = result["server"]["sponsor"]
    s_cc     = result["server"]["cc"]
    s_lat    = result["server"]["latency"]
    share    = result["share"]        

    caption = f"""
<b>⚡ sᴘᴇᴇᴅᴛᴇsᴛ ʀᴇsᴜʟᴛs</b>

<b><u>ᴄʟɪᴇɴᴛ ɪɴғᴏ :</u></b>
<b>❍ ɪsᴘ     :</b> <code>{isp}</code>
<b>❍ ᴄᴏᴜɴᴛʀʏ :</b> <code>{country}</code>

<b><u>sᴇʀᴠᴇʀ ɪɴғᴏ :</u></b>
<b>❍ ɴᴀᴍᴇ    :</b> <code>{server}</code>
<b>❍ sᴘᴏɴsᴏʀ :</b> <code>{sponsor}</code>
<b>❍ ᴄᴏᴜɴᴛʀʏ :</b> <code>{s_cc}</code>
<b>❍ ʟᴀᴛᴇɴᴄʏ :</b> <code>{s_lat} ms</code>

<b><u>sᴘᴇᴇᴅ :</u></b>
<b>❍ ᴘɪɴɢ     :</b> <code>{ping:.2f} ms</code>
<b>❍ ᴅᴏᴡɴʟᴏᴀᴅ :</b> <code>{download:.2f} Mbps</code>
<b>❍ ᴜᴘʟᴏᴀᴅ   :</b> <code>{upload:.2f} Mbps</code>

<b>❍ 𝖡ʏ » <a href="{config.SUPPORT_GROUP}">sʜɪᴢᴜ-ᴍᴜsɪᴄ™</a></b>
"""

    await m.delete()

    # Send speedtest result image with caption
    await message.reply_photo(
        photo=share,
        caption=caption,
        parse_mode=ParseMode.HTML,
        reply_markup=supp_markup(),
    )

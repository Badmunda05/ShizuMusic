# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio

from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

import config
from ShizuMusic import bot, call_py
from ShizuMusic.core.call import leave_vc
from ShizuMusic.core.player import play_song
from ShizuMusic.core.queue import clear_queue, peek_current, pop_current, queue_size
from ShizuMusic.utils.formatters import short
from ShizuMusic.utils.helpers import delete_file
from ShizuMusic.utils.permissions import is_user_authorized


@bot.on_callback_query()
async def on_callback(client, cbq: CallbackQuery) -> None:

    chat_id = cbq.message.chat.id
    user = cbq.from_user
    data = cbq.data

    # ── Admin Check ──────────────────────────
    if data in ("pause", "resume", "skip", "stop", "clear"):

        if not await is_user_authorized(cbq):

            await cbq.answer(
                "❍ ᴀᴅᴍɪɴs ᴏɴʟʏ",
                show_alert=True,
            )
            return

    # ─────────────────────────────────────────
    # PAUSE
    # ─────────────────────────────────────────
    if data == "pause":

        try:
            await call_py.pause(chat_id)

            await cbq.answer("Paused")

            await client.send_message(
                chat_id,
                f"""
<b>❍ sᴛʀᴇᴀᴍ ᴘᴀᴜsᴇᴅ</b>
<b>❍ ʙʏ :</b> {user.mention}
""",
                parse_mode=ParseMode.HTML,
            )

        except Exception:

            await cbq.answer(
                "Failed To Pause",
                show_alert=True,
            )

    # ─────────────────────────────────────────
    # RESUME
    # ─────────────────────────────────────────
    elif data == "resume":

        try:
            await call_py.resume(chat_id)

            await cbq.answer("Resumed")

            await client.send_message(
                chat_id,
                f"""
<b>❍ sᴛʀᴇᴀᴍ ʀᴇsᴜᴍᴇᴅ</b>
<b>❍ ʙʏ :</b> {user.mention}
""",
                parse_mode=ParseMode.HTML,
            )

        except Exception:

            await cbq.answer(
                "Failed To Resume",
                show_alert=True,
            )

    # ─────────────────────────────────────────
    # SKIP
    # ─────────────────────────────────────────
    elif data == "skip":

        if not queue_size(chat_id):

            await cbq.answer(
                "Queue Is Empty",
                show_alert=True,
            )
            return

        skipped = pop_current(chat_id)

        try:
            await call_py.leave_call(chat_id)

        except Exception:
            pass

        await asyncio.sleep(2)

        try:
            delete_file(skipped.get("file_path", ""))

        except Exception:
            pass

        await client.send_message(
            chat_id,
            f"""
<b>❍ ᴛʀᴀᴄᴋ sᴋɪᴘᴘᴇᴅ</b>
<b>❍ ʙʏ :</b> {user.mention}
<b>❍ sᴏɴɢ :</b><code>{short(skipped['title'])}</code>
""",
            parse_mode=ParseMode.HTML,
        )

        nxt = peek_current(chat_id)

        if nxt:

            await cbq.answer("Playing Next")

            dm = await bot.send_message(
                chat_id,
                f"""
<b>❍ ɴᴇxᴛ ᴛʀᴀᴄᴋ :</b><code>{nxt['title']}</code>
""",
                parse_mode=ParseMode.HTML,
            )

            await play_song(chat_id, dm, nxt)

        else:

            await cbq.answer(
                "Queue Empty",
                show_alert=True,
            )

    # ─────────────────────────────────────────
    # STOP
    # ─────────────────────────────────────────
    elif data == "stop":

        await leave_vc(chat_id)

        await cbq.answer("Stopped")

        await client.send_message(
            chat_id,
            f"""
<b>❍ ᴘʟᴀʏʙᴀᴄᴋ sᴛᴏᴘᴘᴇᴅ</b>
<b>❍ ʙʏ :</b> {user.mention}
""",
            parse_mode=ParseMode.HTML,
        )

    # ─────────────────────────────────────────
    # CLEAR
    # ─────────────────────────────────────────
    elif data == "clear":

        clear_queue(chat_id)

        await cbq.answer("Queue Cleared")

        await cbq.message.edit_text(
            f"""
<b>❍ ǫᴜᴇᴜᴇ ᴄʟᴇᴀʀᴇᴅ</b>
<b>❍ ʙʏ :</b> {user.mention}
""",
            parse_mode=ParseMode.HTML,
        )

    # ── Noop (progress bar button) ────────────────────────────────────────────
    elif data == "noop":
        await cbq.answer()

    # ── Help menu ─────────────────────────────────────────────────────────────
    elif data == "show_help":
        await _show_help(cbq)

    elif data == "go_back":
        await _go_back(cbq)

    elif data.startswith("help_"):
        await _help_section(cbq, data)


# ── Help pages ────────────────────────────────────────────────────────────────

async def _go_back(cbq: CallbackQuery) -> None:
    uid  = cbq.from_user.id
    name = cbq.from_user.first_name or "User"
    caption = (
        "<b>╭────────────────────▣</b>\n"
        f"<b>│❍ нєу</b> <a href='tg://user?id={uid}'>{name}</a>, 🥀\n"
        f"<b>│❍ ᴛʜɪs ɪs {config.BOT_NAME} !</b>\n"
        "<b>├────────────────────▣</b>\n"
        "<b>│❍ ᴀ ғᴀsᴛ & ᴘᴏᴡᴇʀғᴜʟ ᴛᴇʟᴇɢʀᴀᴍ ᴍᴜsɪᴄ ʙᴏᴛ.</b>\n"
        "<b>├────────────────────▣</b>\n"
        f"<b>│❍ 𝖯ᴏᴡᴇʀᴇᴅ 𝖡ʏ » <a href=t.me/Alpha_XChats>Aʟᴘʜᴀ-Mᴜsɪᴄ™</a></b>\n"
        "<b>╰────────────────────▣</b>"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⛩️ ᴧᴅᴅ мᴇ ʙᴧʙʏ ⛩️", url=f"{config.BOT_LINK}?startgroup=true")],
        [
            InlineKeyboardButton("🍬 sᴜᴩᴩᴏʀᴛ 🍬", url=config.SUPPORT_GROUP),
            InlineKeyboardButton("🍹 ᴜᴩᴅᴀᴛᴇ 🍹",   url=config.UPDATES_CHANNEL),
        ],
        [InlineKeyboardButton("🏩 ʜᴇʟᴩ ᴧиᴅ ᴄᴏᴍᴍᴧɴᴅs 🏩", callback_data="show_help")],
        [
            InlineKeyboardButton("🫧 ᴏᴡɴᴇʀ 🫧",  url=f"tg://user?id={config.OWNER_ID}"),
            InlineKeyboardButton("🍡 sᴏᴜʀᴄᴇ 🍡", url="https://github.com"),
        ],
    ])
    try:
        await cbq.message.edit_caption(caption=caption, parse_mode=ParseMode.HTML, reply_markup=kb)
    except:
        await cbq.message.edit_text(text=caption, parse_mode=ParseMode.HTML, reply_markup=kb)


async def _show_help(cbq: CallbackQuery) -> None:
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❍ ᴘʟᴀʏ ❍",   callback_data="help_music"),
            InlineKeyboardButton("❍ ᴜᴛɪʟɪᴛʏ ❍", callback_data="help_util"),
        ],
        [InlineKeyboardButton("⌯ ʜᴏᴍᴇ ⌯",    callback_data="go_back")],
        ])
    help_text = "<b>📜 ᴄʜᴏᴏsᴇ ᴀ ᴄᴀᴛᴇɢᴏʀʏ :</b>"
    try:
        await cbq.message.edit_caption(caption=help_text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except:
        await cbq.message.edit_text(text=help_text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def _help_section(cbq: CallbackQuery, data: str) -> None:
    back = InlineKeyboardMarkup([[InlineKeyboardButton("⌯ ʙᴀᴄᴋ ⌯", callback_data="show_help")]])
    texts = {
        "help_music": (
            "<b>╭────────────────────▣</b>\n"
            "<b>│🎵 ᴍᴜsɪᴄ ᴄᴏᴍᴍᴀɴᴅs</b>\n"
            "<b>├────────────────────▣</b>\n"
            "<b>│❍ /play</b> &lt;song or URL&gt;\n"
            "<b>│❍ /pause</b>  — ᴘᴀᴜsᴇ  <i>(ᴀᴅᴍɪɴ)</i>\n"
            "<b>│❍ /resume</b> — ʀᴇsᴜᴍᴇ <i>(ᴀᴅᴍɪɴ)</i>\n"
            "<b>│❍ /skip</b>   — sᴋɪᴩ   <i>(ᴀᴅᴍɪɴ)</i>\n"
            "<b>│❍ /stop</b>   — sᴛᴏᴩ   <i>(ᴀᴅᴍɪɴ)</i>\n"
            "<b>│❍ /clear</b>  — ᴄʟᴇᴀʀ ǫᴜᴇᴜᴇ <i>(ᴀᴅᴍɪɴ)</i>\n"
            "<b>╰────────────────────▣</b>"
        ),
        "help_util": (
            "<b>╭────────────────────▣</b>\n"
            "<b>│🔍 ᴜᴛɪʟɪᴛʏ</b>\n"
            "<b>├────────────────────▣</b>\n"
            "<b>│❍ /ping</b>   — sᴛᴀᴛs & ʟᴀᴛᴇɴᴄʏ\n"
            "<b>│❍ /speedtest</b>  — ɴᴇᴛᴡᴏʀᴋ sᴘᴇᴇᴅ ᴛᴇsᴛ\n"
            "<b>│❍ /spt</b>        — sʜᴏʀᴛᴄᴜᴛ ғᴏʀ sᴘᴇᴇᴅᴛᴇsᴛ\n"
            "<b>│❍ /reboot</b> — ʀᴇsᴇᴛ ᴄʜᴀᴛ sᴛᴀᴛᴇ\n"
            f"<b>│❍ ᴍᴀx sᴏɴɢ: {config.MAX_DURATION_SECONDS // 60} ᴍɪɴᴜᴛᴇs</b>\n"
            "<b>╰────────────────────▣</b>"
        ),
    }
    help_string = texts.get(data, "?")
    try:
        await cbq.message.edit_caption(caption=help_string, parse_mode=ParseMode.HTML, reply_markup=back)
    except:
        await cbq.message.edit_text(text=help_string, parse_mode=ParseMode.HTML, reply_markup=back)
        

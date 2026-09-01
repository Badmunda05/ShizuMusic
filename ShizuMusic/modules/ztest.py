import asyncio
import inspect

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

import config
from ShizuMusic import bot
from ShizuMusic.modules.block import user_allowed
from ShizuMusic.utils.rich_ui import (
    RICH_AVAILABLE,
    rich_details,
    rich_edit,
    rich_heading,
    rich_send,
    rich_table,
)

OWNER_ID = config.OWNER_ID


# ── /testrich ──────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("testrich") & user_allowed)
async def test_rich_handler(_, message: Message) -> None:

    uid = message.from_user.id

    # ── Delete the command message ─────────────────────────────────────────────
    try:
        await message.delete()
    except Exception:
        pass

    if uid != OWNER_ID:
        return

    chat_id = message.chat.id

    # ── Static checks (no network calls) ───────────────────────────────────────
    static_lines = [f"<b>🧪 Rich message capability check</b>\n"]

    import pyrogram
    static_lines.append(f"<b>❍ Package version :</b> <code>{getattr(pyrogram, '__version__', 'unknown')}</code>")

    try:
        from pyrogram.types import InputRichMessage
        params = list(inspect.signature(InputRichMessage.__init__).parameters)
        static_lines.append(f"<b>❍ InputRichMessage :</b> ✔️ params=<code>{params}</code>")
    except ImportError:
        static_lines.append("<b>❍ InputRichMessage :</b> ✘ not found in this build")

    from pyrogram import Client
    if hasattr(Client, "send_rich_message"):
        static_lines.append("<b>❍ send_rich_message :</b> ✔️ exists")
    else:
        static_lines.append("<b>❍ send_rich_message :</b> ✘ not found")

    if hasattr(Client, "edit_message_text"):
        edit_params = list(inspect.signature(Client.edit_message_text).parameters)
        has_rich_kw = "rich_message" in edit_params
        static_lines.append(
            f"<b>❍ edit_message_text('rich_message=') :</b> "
            f"{'✔️ present' if has_rich_kw else '✘ not in signature'}"
        )
    else:
        static_lines.append("<b>❍ edit_message_text :</b> ✘ not found")

    static_lines.append(f"<b>❍ rich_ui.RICH_AVAILABLE :</b> <code>{RICH_AVAILABLE}</code>")

    await bot.send_message(chat_id, "\n".join(static_lines), parse_mode=ParseMode.HTML)

    if not RICH_AVAILABLE:
        await bot.send_message(
            chat_id,
            "<b>⚠️ RICH_AVAILABLE is False</b> — the live test below will use the "
            "classic plain-text fallback for everything. Still worth watching to "
            "confirm the fallback itself looks right.",
            parse_mode=ParseMode.HTML,
        )

    # ── Live test #1: send ───────────────────────────────────────────────────────
    test_html_1 = (
        rich_heading("🧪 Rich message test #1", level=3)
        + "<p>If this shows as a real heading (bigger/bold, on its own line — "
          "not the literal text \"h3\"), rich sending works.</p>"
        + rich_table(["Check", "Expect"], [
            ("Heading above", "Rendered as a real section heading"),
            ("This table", "Rendered as an actual bordered table"),
        ])
        + rich_details("Tap to expand", "<p>If this text was hidden until you "
                        "tapped 'Tap to expand', collapsible details work too.</p>")
    )

    sent = await rich_send(bot, chat_id, test_html_1)
    if sent is None:
        await bot.send_message(
            chat_id,
            "<b>✘ rich_send returned None</b> — sending failed even with the "
            "plain-text fallback. Check bot permissions in this chat.",
            parse_mode=ParseMode.HTML,
        )
        return

    await bot.send_message(
        chat_id,
        f"<b>✔️ Sent test message #1</b> (id <code>{sent.id}</code>). "
        "Scroll up and look at it now — real heading/table/details, or plain "
        "text with literal tags?",
        parse_mode=ParseMode.HTML,
    )

    await asyncio.sleep(3)

    # ── Live test #2: edit ────────────────────────────────────────────────────────
    test_html_2 = (
        rich_heading("🧪 Rich message test #2 (edited)", level=3)
        + "<p>This replaced test #1 via <code>rich_edit()</code>. If the "
          "message above changed in place — same message, new content — "
          "editing rich content works.</p>"
    )

    edited = await rich_edit(sent, test_html_2)
    if edited is None:
        await bot.send_message(
            chat_id,
            "<b>⚠️ rich_edit returned None</b> — could be a real failure, or "
            "Telegram said 'message not modified' (harmless). Check the "
            "message above directly.",
            parse_mode=ParseMode.HTML,
        )
    else:
        await bot.send_message(
            chat_id,
            "<b>✔️ rich_edit did not raise.</b> Confirm above that the message "
            "text actually changed.",
            parse_mode=ParseMode.HTML,
        )

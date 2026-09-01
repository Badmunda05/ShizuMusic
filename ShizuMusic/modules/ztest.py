# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------
#
#  /testrich — owner-only diagnostic command. Sends a real rich test message
#  (heading + table + collapsible details) into the chat, waits, then edits
#  it. Reminder: "no exception raised" isn't proof it worked — a silently
#  ignored kwarg wouldn't raise either. Always check what actually rendered
#  in Telegram, not just whether this command finished without error.
# --------------------------------------------------------------------------------

import asyncio
import inspect

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

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

    # ── Live test #1: send (with buttons — see the edit test below for the
    #    actual "buttons cut on edit" fix) ────────────────────────────────────
    test_kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🍬 Support", url=getattr(config, "SUPPORT_GROUP", "https://t.me")),
            InlineKeyboardButton("🍹 Updates", url=getattr(config, "UPDATES_CHANNEL", "https://t.me")),
        ],
    ])

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

    sent = await rich_send(bot, chat_id, test_html_1, reply_markup=test_kb)
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
    # THE "BUTTONS CUT ON EDIT" FIX: Telegram's edit_message_text (rich or plain)
    # does NOT keep the previous message's reply_markup automatically — if you
    # don't pass reply_markup again on the edit call, the buttons disappear.
    # The original version of this test called rich_edit(sent, test_html_2)
    # with no reply_markup at all, which is exactly why the keyboard vanished
    # after the edit. Re-passing test_kb below keeps the buttons attached.
    test_html_2 = (
        rich_heading("🧪 Rich message test #2 (edited)", level=3)
        + "<p>This replaced test #1 via <code>rich_edit()</code>. If the "
          "message above changed in place — same message, new content, "
          "<b>and the Support/Updates buttons are still there</b> — editing "
          "rich content + keeping buttons works.</p>"
    )

    edited = await rich_edit(sent, test_html_2, reply_markup=test_kb)
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
            "text changed AND the Support/Updates buttons are still visible "
            "(that's the part that was 'cut' before).",
            parse_mode=ParseMode.HTML,
        )

    await asyncio.sleep(2)

    # ── Live test #3: every tag from the official formatting example ────────────
    # Sent as raw HTML (not via the rich_ui.py helpers) so this is a direct,
    # unmodified test of the tags themselves — if one breaks, it tells us
    # whether rich_ui.py's own builders (e.g. rich_button) need fixing to
    # match, rather than hiding a mismatch behind the helper.
    #
    # NOTE ON tg-button's "type" ATTRIBUTE: rich_ui.py's rich_button() builds
    # <tg-button url="..."> / <tg-button callback_data="..."> WITHOUT a
    # type="..." attribute. This test uses type="..." explicitly (matching
    # the official example you showed). If test #3a renders correctly and
    # rich_button()'s output doesn't, that's the fix needed in rich_ui.py —
    # this test is what will tell us either way.
    await bot.send_message(
        chat_id,
        "<b>🧪 Test #3a — text formatting + media/layout tags</b>\n"
        "(map / collage / slideshow use Telegram's own example URLs — expect "
        "those specific ones to possibly fail to load as images/video, that's "
        "normal; the point is whether the *blocks* render as maps/collages "
        "at all, not whether that exact demo photo loads)",
        parse_mode=ParseMode.HTML,
    )

    test_html_3a = (
        "<p><u>underlined text</u>, <ins>underlined text</ins></p>"
        "<p>H<sub>2</sub>O and E=mc<sup>2</sup></p>"
        '<p><a name="chapter-1"></a>Anchor set above (jump target — not '
        "independently visible, just shouldn't error)</p>"
        "<aside>Pull quote<cite>The Author</cite></aside>"
        "<details open><summary>Title</summary>Content</details>"
        '<tg-map lat="41.9" long="12.5" zoom="14"/>'
        '<tg-collage><img src="https://telegram.org/img/t_logo.png"/>'
        "<figcaption>Caption<cite>The Author</cite></figcaption></tg-collage>"
        '<tg-slideshow><img src="https://telegram.org/img/t_logo.png"/>'
        "<figcaption>Slideshow caption<cite>The Author</cite></figcaption>"
        "</tg-slideshow>"
    )
    sent_3a = await rich_send(bot, chat_id, test_html_3a)
    await bot.send_message(
        chat_id,
        "<b>✔️ Test #3a sent</b>" if sent_3a else "<b>✘ Test #3a failed to send</b>",
        parse_mode=ParseMode.HTML,
    )

    await asyncio.sleep(1)

    await bot.send_message(
        chat_id,
        "<b>🧪 Test #3b — every &lt;tg-button&gt; type + tg-time + tg-emoji</b>\n"
        "web_app only works in private chats; login_url needs a domain set "
        "via @BotFather on this bot; switch_inline_query needs inline mode "
        "enabled. Expect those specific buttons to be the likely failure "
        "points, not the whole message.",
        parse_mode=ParseMode.HTML,
    )

    test_html_3b = (
        "<p>Inline buttons:<br/>"
        '<tg-button type="url" style="success" url="https://t.me">url</tg-button> '
        '<tg-button type="url" url="tg://user?id=777000">user</tg-button><br/>'
        '<tg-button type="callback_data" style="link" data="testrich_cb">'
        "callback with the date "
        '<tg-time unix="1647531900" format="wDT">22:45 tomorrow</tg-time> '
        "and the custom emoji "
        '<tg-emoji emoji-id="5368324170671202286">👍</tg-emoji>'
        "</tg-button><br/>"
        '<tg-button type="web_app" style="danger" url="https://telegram.org">'
        "Mini App (private chats only)</tg-button><br/>"
        '<tg-button type="login_url" url="https://t.me" forward-text="forward text" '
        'request-write-access>login (needs a domain set via @BotFather)</tg-button><br/>'
        '<tg-button type="switch_inline_query" style="primary" query="inline">'
        "inline</tg-button> "
        '<tg-button type="switch_inline_query_current_chat" query="inline 2">'
        "inline 2</tg-button> "
        '<tg-button type="switch_inline_query_chosen_chat" query="inline 3" '
        'allow-user-chats allow-bot-chats allow-group-chats allow-channel-chats>'
        "inline 3</tg-button><br/>"
        '<tg-button type="copy_text" text="...copy">Copy</tg-button> '
        '<tg-button type="disabled">Disabled</tg-button>'
        "</p>"
    )
    sent_3b = await rich_send(bot, chat_id, test_html_3b)
    await bot.send_message(
        chat_id,
        "<b>✔️ Test #3b sent</b> — tap each button and note which ones actually "
        "fire vs. do nothing/error." if sent_3b else "<b>✘ Test #3b failed to send</b>",
        parse_mode=ParseMode.HTML,
    )

    await asyncio.sleep(2)

    # ── Live test #4: embedded tg-button (inside the bubble) + classic
    #    reply_markup (separate rows below the bubble) on the SAME message —
    #    no edit this time, just one send, so the two button styles can be
    #    compared directly like in your reference screenshots:
    #      • tg-button tags in the HTML body render as pill buttons INSIDE
    #        the message bubble, right after the text.
    #      • reply_markup=InlineKeyboardMarkup(...) renders as full-width
    #        button rows BELOW the bubble, same as any classic message.
    #    They're two independent mechanisms — a message can use either, or
    #    both at once, as tested here.
    await bot.send_message(
        chat_id,
        "<b>🧪 Test #4 — embedded tg-button (in-bubble) + classic reply_markup "
        "(below-bubble) on one message</b>\n"
        "Look for TWO different button styles: small pill buttons inside the "
        "text itself, and full-width rows below the message.",
        parse_mode=ParseMode.HTML,
    )

    test_html_4 = (
        rich_heading("🧪 Test #4", level=3)
        + "<p>Everything below the divider is a <tg-button> tag embedded "
          "directly in this rich message's HTML — it should render "
          "<b>inside this bubble</b>, not as a separate keyboard.</p>"
        + "<p>"
        + '<tg-button type="url" style="success" url="https://t.me">'
        "In-bubble: url</tg-button> "
        '<tg-button type="callback_data" style="primary" data="testrich_inbubble">'
        "In-bubble: callback</tg-button>"
        + "</p>"
    )

    classic_kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Below-bubble: url", url="https://t.me"),
            InlineKeyboardButton("Below-bubble: callback", callback_data="testrich_belowbubble"),
        ],
    ])

    sent_4 = await rich_send(bot, chat_id, test_html_4, reply_markup=classic_kb)
    await bot.send_message(
        chat_id,
        "<b>✔️ Test #4 sent</b> — go look: are there really two visually "
        "distinct button groups (in-bubble pills + below-bubble rows), or "
        "did the tg-button tags just get stripped/ignored and only the "
        "classic reply_markup buttons showed up?" if sent_4 else
        "<b>✘ Test #4 failed to send</b>",
        parse_mode=ParseMode.HTML,
    )

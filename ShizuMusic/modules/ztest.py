# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
# --------------------------------------------------------------------------------

from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from ShizuMusic import bot
from ShizuMusic.modules.block import user_allowed
from ShizuMusic.utils.rich_ui import (
    rich_details,
    rich_heading,
    rich_send,
    rich_table,
)

OWNER_ID = config.OWNER_ID


@bot.on_message(filters.command("testrich") & user_allowed)
async def test_rich_handler(_, message: Message) -> None:

    # Delete command message
    try:
        await message.delete()
    except Exception:
        pass

    # Owner only
    if message.from_user.id != OWNER_ID:
        return

    chat_id = message.chat.id

    # Buttons
    test_kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🍬 Support",
                url=getattr(config, "SUPPORT_GROUP", "https://t.me")
            ),
            InlineKeyboardButton(
                "🍹 Updates",
                url=getattr(config, "UPDATES_CHANNEL", "https://t.me")
            ),
        ]
    ])

    # Rich Message Test #1
    test_html = (
        rich_heading("🧪 Rich message test #1", level=3)
        + "<p>If this shows as a real heading (bigger/bold, on its own line — "
          "not the literal text \"h3\"), rich sending works.</p>"
        + rich_table(
            ["Check", "Expect"],
            [
                ("Heading above", "Rendered as a real section heading"),
                ("This table", "Rendered as an actual bordered table"),
            ]
        )
        + rich_details(
            "Tap to expand",
            "<p>If this text was hidden until you tapped "
            "'Tap to expand', collapsible details work too.</p>"
        )
    )

    # Send rich message
    sent = await rich_send(
        bot,
        chat_id,
        test_html,
        reply_markup=test_kb
    )

    if sent is None:
        await bot.send_message(
            chat_id,
            "❌ Rich message test failed."
        )
        return

    await bot.send_message(
        chat_id,
        f"✅ Rich message test sent successfully.\n\n"
        f"Message ID: `{sent.id}`"
    )


# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Rich menu example — tg-button style="primary"/"success"/"danger"
# --------------------------------------------------------------------------------

from pyrogram import filters, Client
from pyrogram.types import Message, CallbackQuery

import config
from ShizuMusic import bot
from ShizuMusic.modules.block import user_allowed
from ShizuMusic.utils.rich_ui import (
    rich_heading,
    rich_button,
    rich_send,
    rich_reply,
)

OWNER_ID = config.OWNER_ID


@bot.on_message(filters.command("menu") & user_allowed)
async def rich_menu_handler(_, message: Message) -> None:

    try:
        await message.delete()
    except Exception:
        pass

    chat_id = message.chat.id

    # Build menu with rich styled buttons using <tg-button> tags
    # These render as colored inline buttons in the message (requires Bot API 10.3+)
    menu_html = (
        rich_heading("📋 Main Menu", level=3)
        + "<p>"
        + rich_button("🎵 Play", callback_data="menu_play", style="primary")   # blue
        + " "
        + rich_button("⚙️ Settings", callback_data="menu_settings", style="success")  # green
        + " "
        + rich_button("🗑 Stop", callback_data="menu_stop", style="danger")    # red
        + "</p>"
        + "<p>"
        + rich_button("🍬 Support", url=getattr(config, "SUPPORT_GROUP", "https://t.me"), style="primary")
        + " "
        + rich_button("🍹 Updates", url=getattr(config, "UPDATES_CHANNEL", "https://t.me"), style="success")
        + "</p>"
    )

    sent = await rich_send(bot, chat_id, menu_html)

    if sent is None:
        await bot.send_message(chat_id, "❌ Menu send failed.")
        return

    await bot.send_message(chat_id, f"✅ Menu sent! (Message ID: {sent.id})")


# ─────────────────────────────────────────────────────────────────────────────
# Callback handlers for menu buttons
# ─────────────────────────────────────────────────────────────────────────────

@bot.on_callback_query(filters.regex("^menu_play"))
async def menu_play_cb(client: Client, callback_query: CallbackQuery) -> None:
    await rich_reply(
        callback_query,
        rich_heading("🎵 Now Playing", level=3) + "<p>Music playback started!</p>"
    )


@bot.on_callback_query(filters.regex("^menu_settings"))
async def menu_settings_cb(client: Client, callback_query: CallbackQuery) -> None:
    await rich_reply(
        callback_query,
        rich_heading("⚙️ Settings", level=3) + "<p>Settings panel opened.</p>"
    )


@bot.on_callback_query(filters.regex("^menu_stop"))
async def menu_stop_cb(client: Client, callback_query: CallbackQuery) -> None:
    await rich_reply(
        callback_query,
        rich_heading("🗑 Stopped", level=3) + "<p>Playback stopped.</p>"
    )

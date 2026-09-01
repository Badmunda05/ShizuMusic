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
    #
    # Two different button styles on purpose, so you can compare them:
    #   - test_kb (below)      -> classic reply_markup, renders as plain rows
    #                              BELOW the message bubble.
    #   - the <tg-button> pair  -> embedded directly in the rich HTML content,
    #     in test_html below       should render as colored pill buttons
    #                              INSIDE the bubble (blue "Support",
    #                              green "Updates") — like the Support™ /
    #                              BabiesIQ™ pills in the reference screenshot.
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
        + "<p>"
        + f'<tg-button type="url" style="primary" url="{getattr(config, "SUPPORT_GROUP", "https://t.me")}">'
          "🍬 Support</tg-button> "
        + f'<tg-button type="url" style="success" url="{getattr(config, "UPDATES_CHANNEL", "https://t.me")}">'
          "🍹 Updates</tg-button>"
        + "</p>"
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
        f"Message ID: `{sent.id}`\n\n"
        "Check the message above for TWO different button looks:\n"
        "• Colored pill buttons (blue Support, green Updates) *inside* the "
        "bubble, right under the table — those are the embedded <tg-button> "
        "tags.\n"
        "• Plain rows *below* the bubble — that's the classic reply_markup "
        "keyboard."
    )

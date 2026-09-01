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

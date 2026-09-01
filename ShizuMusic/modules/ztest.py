# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
# --------------------------------------------------------------------------------

from pyrogram import enums, filters
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

    # Buttons — style= is a REAL InlineKeyboardButton kwarg (confirmed against
    # kurigram's source: pyrogram/types/bots_and_keyboards/inline_keyboard_button.py),
    # backed by enums.ButtonStyle. No tg-button/HTML trick needed for color —
    # this colors the classic reply_markup buttons directly.
    #   DEFAULT = normal grey · PRIMARY = dark blue · DANGER = red · SUCCESS = green
    test_kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🍬 Support",
                url=getattr(config, "SUPPORT_GROUP", "https://t.me"),
                style=enums.ButtonStyle.PRIMARY,
            ),
            InlineKeyboardButton(
                "🍹 Updates",
                url=getattr(config, "UPDATES_CHANNEL", "https://t.me"),
                style=enums.ButtonStyle.SUCCESS,
            ),
        ]
    ])

    # Rich Message Test #1
    #
    # Two independent, both-colored button mechanisms on purpose, so you can
    # compare them directly:
    #   - test_kb (above)       -> classic reply_markup with the native
    #                              style= kwarg. Renders as colored rows
    #                              BELOW the message bubble (blue Support,
    #                              green Updates) — no HTML/tg-button needed.
    #   - the <tg-button> pair   -> embedded directly in the rich HTML content,
    #     in test_html below        should render as colored pill buttons
    #                              INSIDE the bubble instead.
    # If both show up colored in their respective spot, both mechanisms work.
    # If only the below-bubble ones are colored, tg-button styling isn't
    # supported yet on this build and style= is the one to actually use.
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

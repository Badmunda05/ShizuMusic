import random
from pyrogram import filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
import config
from ShizuMusic import bot

# Fireworks effects
EFFECT_ID = [
    5046509860389126442,
    5107584321108051014,
    5104841245755180586,
    5159385139981059251,
]

@bot.on_message(filters.command("start"))
async def start_handler(_, message: Message) -> None:
    uid = message.from_user.id
    name = message.from_user.first_name or "User"
    chat_id = message.chat.id
    chat_type = message.chat.type

    # Database logic
    try:
        from ShizuMusic.database import add_served_user, add_served_chat
        add_served_user(uid)
        add_served_chat(chat_id)
    except:
        pass

    if chat_type == ChatType.PRIVATE:
        # EXACT PHOTO DESIGN
        caption = (
            "┌───╼\n"
            f"❍ **ʜᴇʏ** [{name}](tg://user?id={uid}), 🥀\n"
            f"❍ **ᴛʜɪs ɪs ———✨{config.BOT_NAME} ✨ !**\n"
            "┝───╼\n"
            "❍ **ᴀ ғᴀsᴛ & ᴘᴏᴡᴇʀғᴜʟ ᴛᴇʟᴇɢʀᴀᴍ**\n"
            "**ᴍᴜsɪᴄ ᴘʟᴀʏᴇʀ ʙᴏᴛ ᴡɪᴛʜ**\n"
            "**sᴏᴍᴇ ᴀᴡᴇsᴏᴍᴇ ғᴇᴀᴛᴜʀᴇs.**\n"
            "┝───╼\n"
            "❍ **ᴄʟɪᴄᴋ ʜᴇʟᴘ ғᴏʀ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs.**\n"
            "┝───╼\n"
            f"❍ **ᴘᴏᴡᴇʀᴇᴅ ʙʏ » [Aʟᴘʜᴀ-Mᴜsɪᴄ™]({config.SUPPORT_GROUP})**\n"
            "└───╼"
        )
        
        bot_obj = await bot.get_me()
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("⛩️ ᴧᴅᴅ мᴇ ʙᴧʙʏ ⛩️", url=f"https://t.me/{bot_obj.username}?startgroup=true")],
            [
                InlineKeyboardButton("🍬 sᴜᴘᴘᴏʀᴛ 🍬", url=config.SUPPORT_GROUP),
                InlineKeyboardButton("🍹 ᴜᴘᴅᴀᴛᴇs 🍹",  url=config.UPDATES_CHANNEL),
            ],
            [InlineKeyboardButton("🏩 ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs 🏩", callback_data="show_help")],
            [
                InlineKeyboardButton("🫧 ᴏᴡɴᴇʀ 🫧",  url=f"tg://openmessage?user_id={config.OWNER_ID}"),
                InlineKeyboardButton("🍡 sᴏᴜʀᴄᴇ 🍡", url="https://github.com/TeamDevil05/AlphaMusic"),
            ],
        ])

        await message.reply_animation(
            config.START_ANIMATION,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb,
            message_effect_id=random.choice(EFFECT_ID),
        )

        # Logger Notification for Private Start
        if config.LOGGER_ID:
            try:
                await bot.send_message(
                    config.LOGGER_ID,
                    f"<b>#ɴᴇᴡ_ᴜsᴇʀ_sᴛᴀʀᴛᴇᴅ</b>\n\n"
                    f"<b>❍ ɴᴀᴍᴇ:</b> {name}\n"
                    f"<b>❍ ɪᴅ:</b> <code>{uid}</code>\n"
                    f"<b>❍ ᴜsᴇʀɴᴀᴍᴇ:</b> @{message.from_user.username or 'N/A'}",
                    parse_mode=ParseMode.HTML,
                )
            except:
                pass

    else:
        # Group logic
        await message.reply_text(f"❍ ʜᴇʏ {name}, ᴛʜɪs ɪs {config.BOT_NAME}. I'm Alive!")
        
        # Logger Notification for Group Start
        if config.LOGGER_ID:
            try:
                await bot.send_message(
                    config.LOGGER_ID,
                    f"<b>#ɴᴇᴡ_ɢʀᴏᴜᴘ_ᴀᴅᴅᴇᴅ</b>\n\n"
                    f"<b>❍ ɢʀᴏᴜᴘ ɴᴀᴍᴇ:</b> {message.chat.title}\n"
                    f"<b>❍ ɢʀᴏᴜᴘ ɪᴅ:</b> <code>{chat_id}</code>\n"
                    f"<b>❍ ᴀᴅᴅᴇᴅ ʙʏ:</b> {name}",
                    parse_mode=ParseMode.HTML,
                )
            except:
                pass
                

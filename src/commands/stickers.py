import random

from config import bot, templates


def handle_stickers(message):
    bot.send_sticker(
        message.chat.id,
        random.choice(templates["sticker_to_sticker"].get(message.sticker.file_id)),
        reply_to_message_id=message.message_id,
    )

import random

from config import bot, templates


def handle_stickers(answers):
    return lambda message: bot.send_sticker(
        message.chat.id,
        random.choice(answers.get(message.sticker.file_id)),
        reply_to_message_id=message.message_id,
    )

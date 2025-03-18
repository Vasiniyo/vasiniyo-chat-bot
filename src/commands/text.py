import random

from config import bot, templates
from constants import ANDRUXA_TANENBAUM_PHRASES, IS_TANENBAUM, MESSAGE_MAX_LEN


def handle_text(message):
    user_message = message.text.lower()

    if len(user_message) > MESSAGE_MAX_LEN:
        __to_long_message(message)
    elif reply := templates["text_to_text"].get(user_message):
        reply = __get_tanenbaum_phrase(user_message)
        bot.reply_to(message, reply)
    elif sticker_file_id := templates["text_to_sticker"].get(user_message):
        bot.send_sticker(
            message.chat.id, sticker_file_id, reply_to_message_id=message.message_id
        )


def __to_long_message(message):
    bot.reply_to(message, "Многа букав, не осилил!")


def __get_tanenbaum_phrase(message):
    if message == IS_TANENBAUM:
        return random.choice(ANDRUXA_TANENBAUM_PHRASES)
    return message

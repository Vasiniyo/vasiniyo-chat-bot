import logging
import random

from config import bot, templates
from constansts import IS_TANENBAUM, ANDRUXA_TANENBAUM_PHRASES, TANENBAUM_RANGE

logger = logging.getLogger(__name__)


@bot.message_handler(func=lambda message: True)
def reply_text(message):
    user_message = message.text.lower()
    if reply := templates["text_to_text"].get(user_message):
        reply = __get_tanenbaum_phrase(user_message)
        bot.reply_to(message, reply)
    elif sticker_file_id := templates["text_to_sticker"].get(user_message):
        bot.send_sticker(
            message.chat.id, sticker_file_id, reply_to_message_id=message.message_id
        )


@bot.message_handler(content_types=["sticker"])
def reply_sticker(message):
    if sticker_file_id := templates["sticker_to_sticker"].get(message.sticker.file_id):
        bot.send_sticker(
            message.chat.id, sticker_file_id, reply_to_message_id=message.message_id
        )


def __get_tanenbaum_phrase(message):
    if message == IS_TANENBAUM:
        return ANDRUXA_TANENBAUM_PHRASES.get(random.randint(*TANENBAUM_RANGE))
    return message


if __name__ == "__main__":
    logger.info("Bot started")
    bot.polling()
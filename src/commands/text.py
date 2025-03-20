import logging
import random

from config import bot, templates
from constants import ANDRUXA_TANENBAUM_PHRASES, IS_TANENBAUM, MESSAGE_MAX_LEN

from .fuzzy_match.fuzzy_match import test_match

logger = logging.getLogger(__name__)


def handle_text(message):
    user_message = message.text

    if len(user_message) > MESSAGE_MAX_LEN:
        logger.info(
            "Слишком длинное сообщение от пользователя %s", message.from_user.id
        )
        __to_long_message(message)
        return

    found, matched_key, used_inverted = test_match(user_message, "text_to_text")
    if found:
        logger.info("Совпадение text_to_text: %s", matched_key)
        if matched_key == IS_TANENBAUM:
            reply = random.choice(ANDRUXA_TANENBAUM_PHRASES)
        else:
            reply = templates["text_to_text"].get(matched_key)

        if used_inverted:
            reply = f"(Вы имели в виду: {matched_key}?)\n{reply}"

        bot.reply_to(message, reply)
        return

    found, matched_key, used_inverted = test_match(user_message, "text_to_sticker")
    if found:
        logger.info("Совпадение text_to_sticker: %s", matched_key)
        sticker_file_id = templates["text_to_sticker"][matched_key]
        if used_inverted:
            bot.reply_to(message, f"(Вы имели в виду: {matched_key}?)")

        bot.send_sticker(
            message.chat.id, sticker_file_id, reply_to_message_id=message.message_id
        )
        return


def __to_long_message(message):
    bot.reply_to(message, "Многа букав, не осилил!")

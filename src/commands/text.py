import logging
import random

from config import MESSAGE_MAX_LEN, bot

from .fuzzy_match.fuzzy_match import test_match

logger = logging.getLogger(__name__)


def handle_long(answers):
    return lambda message: bot.reply_to(message, random.choice(answers))

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

def handle_text_to_text(answers):
    def inner(message):
        matched_key, reply, used_inverted = __get_response(message, answers)
        if used_inverted:
            reply = f"{matched_key}?\n{reply}"
        bot.reply_to(message, reply)

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


def handle_text_to_sticker(answers):
    return lambda message: bot.send_sticker(
        message.chat.id,
        __get_response(message, answers)[1],
        reply_to_message_id=message.message_id,
    )


def __get_response(message, answers):
    matched_key, used_inverted = test_match(message.text, answers.keys())
    return matched_key, random.choice(answers.get(matched_key)), used_inverted

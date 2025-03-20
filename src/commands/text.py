import random

from config import MESSAGE_MAX_LEN, bot, templates

from .fuzzy_match.fuzzy_match import test_match


def handle_long(message):
    bot.reply_to(message, "Многа букав, не осилила!")


def handle_text_to_text(message):
    matched_key, reply, used_inverted = __get_response(message, "text_to_text")
    if used_inverted:
        reply = f"{matched_key}?\n{reply}"
    bot.reply_to(message, reply)


def handle_text_to_sticker(message):
    bot.send_sticker(
        message.chat.id,
        __get_response(message, "text_to_sticker")[1],
        reply_to_message_id=message.message_id,
    )


def __get_response(message, res_type):
    matched_key, used_inverted = test_match(message.text, res_type)
    return (
        matched_key,
        random.choice(templates[res_type].get(matched_key)),
        used_inverted,
    )

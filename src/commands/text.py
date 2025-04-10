import random

from config import MESSAGE_MAX_LEN, bot

from .fuzzy_match.fuzzy_match import choice_one_match


def handle_long(answers):
    return lambda message: bot.reply_to(message, random.choice(answers))


def handle_text_to_text(answers):
    def inner(message):
        matched_key, reply, used_inverted = __get_response(message, answers)
        if used_inverted:
            reply = f"{matched_key}?\n{reply}"
        bot.reply_to(message, reply)

    return inner


def handle_text_to_sticker(answers):
    return lambda message: bot.send_sticker(
        message.chat.id,
        __get_response(message, answers)[1],
        reply_to_message_id=message.message_id,
    )


def __get_response(message, answers):
    matched_key, used_inverted = choice_one_match(message.text, answers.keys())
    return matched_key, random.choice(answers.get(matched_key)), used_inverted

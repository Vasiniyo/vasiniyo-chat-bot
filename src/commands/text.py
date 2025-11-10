import random

import safely_bot_utils as bot

from .fuzzy_match.fuzzy_match import choice_one_match


def handle_long(answers):
    return lambda m: bot.reply_to(random.choice(answers))(m)


def handle_text_to_text(answers):
    def inner(message):
        reply = __get_reply(message, answers)
        bot.reply_to(reply)(message)

    return inner


def handle_text_to_sticker(answers):
    return lambda m: bot.send_sticker(__get_response(m, answers)[1])(m)


def handle_text_to_text_to_target(answers):
    def inner(message):
        reply = __get_reply(message, answers)
        if message.reply_to_message is not None:
            message = message.reply_to_message
        bot.reply_to(reply)(message)

    return inner


def __get_reply(message, answers):
    matched_key, reply, used_inverted = __get_response(message, answers)
    if used_inverted:
        reply = f"{matched_key}?\n{reply}"
    return reply


def __get_response(message, answers):
    matched_key, used_inverted = choice_one_match(message.text, answers.keys())
    return matched_key, random.choice(answers.get(matched_key)), used_inverted

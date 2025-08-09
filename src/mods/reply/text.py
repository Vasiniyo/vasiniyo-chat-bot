import random

from commands.fuzzy_match.fuzzy_match import choice_one_match
from commands.utils import handler, head
from config import text_to_sticker, text_to_text
import safely_bot_utils as bot

from ..register import reg_handler

message_ok = lambda t: lambda m: head(choice_one_match(m.text, t.keys()))


# ========== HANDLERS =========================================================


@reg_handler(handler(message_ok(text_to_text)), text_to_text)
def handle_text_to_text(answers):
    def inner(message):
        matched_key, reply, used_inverted = __get_response(message, answers)
        if used_inverted:
            reply = f"{matched_key}?\n{reply}"
        bot.reply_to(reply)(message)

    return inner


@reg_handler(handler(message_ok(text_to_sticker)), text_to_sticker)
def handle_text_to_sticker(answers):
    return lambda m: bot.send_sticker(__get_response(m, answers)[1])(m)


# ========== private functions ================================================


def __get_response(message, answers):
    matched_key, used_inverted = choice_one_match(message.text, answers.keys())
    return matched_key, random.choice(answers.get(matched_key)), used_inverted

import logging
from math import e
from random import random

from telebot.types import Message, Sticker

from captcha_manager import (
    CAPTCHA_USERS,
    handle_captcha_button_press,
    handle_new_user,
    handle_user_left,
    handle_verify_captcha,
)
from commands.anime import handle_anime
from commands.drink_or_not import handle_drink_or_not
from commands.event import handle_top_espers, play, send_players
from commands.help import handle_help, handle_inline_help, handle_unknown
from commands.how_much import handle_how_much
from commands.like import handle_like, handle_top_likes
from commands.roll_custom_title import handle_title_change_attempt, prepare_game, start
from commands.stickers import handle_stickers
from commands.text import (
    handle_long,
    handle_text_to_sticker,
    handle_text_to_text,
    handle_text_to_text_to_target,
)
from config import config
import safely_bot_utils as bot

from .fuzzy_match.fuzzy_match import choice_one_match
from .roll_custom_title import validate_data

head = lambda l: l[0] if l else None
at = lambda l: lambda n: l[n] if n < len(l) else None

in_allowed_chat = lambda m: any(
    ["*" in config.allowed_chat_ids, str(m.chat.id) in config.allowed_chat_ids]
)
cmd_name = lambda m: head(split_cmd(m))
split_cmd = lambda m: head(m.text.lstrip("/").split()).split("@")
is_cmd_for_bot = lambda c: any([at(c)(1) is None, is_bot_username(c)])
is_bot_username = lambda c: at(c)(1) == bot.get_me().username
unknown_cmd = (
    lambda c: head(c) == "@"
    and is_bot_username(c)
    and head(c) not in list(COMMANDS.keys())
)

chat_ok = lambda p: lambda m: p(m) and in_allowed_chat(m)
message_ok = lambda t: lambda m: head(choice_one_match(m.text, t.keys()))
message_ok_and_equal = lambda t: lambda m: m.text.lower() in map(
    lambda text: text.lower(), config.triggerReplies.text_to_text_to_target
)
sticker_ok = lambda t: lambda m: m.sticker.file_id in t.keys()
cmd_ok = lambda m: is_cmd_for_bot(split_cmd(m)) and not is_captcha_user(m)
cmd_no_ok = lambda m: unknown_cmd(split_cmd(m))
is_captcha_user = lambda m: m.from_user.id in CAPTCHA_USERS


def filter_modules(modules):
    res = {}
    for mod in modules:
        if mod not in config.mods:
            logging.warning(f"Module [{mod}] is not included")
        else:
            for key, value in modules[mod].items():
                res[key] = value
    return res


COMMANDS = filter_modules(
    {
        "core": {"help": (None, bot.phrases("help_help"))},
        "anime": {"anime": (handle_anime, bot.phrases("anime_help"))},
        "likes": {
            "top_likes": (handle_top_likes, bot.phrases("top_likes_help")),
            "like": (handle_like, bot.phrases("like_help")),
        },
        "roll_title": {
            "rename": (prepare_game, bot.phrases("rename_help")),
            "reg": (start, bot.phrases("reg_help")),
        },
        "drink_or_not": {
            "drink_or_not": (
                handle_drink_or_not(config.drinks),
                bot.phrases("drink_or_not_help"),
            )
        },
        "how_much": {
            "how_much_esper": (
                handle_how_much(config.espers),
                bot.phrases("how_much_esper_help"),
            )
        },
        "event": {
            "top_espers": (handle_top_espers, bot.phrases("top_espers_help")),
            "players": (send_players, bot.phrases("players_help")),
            "play": (play, bot.phrases("play_help")),
        },
    }
)
COMMANDS["help"] = (handle_help(COMMANDS), COMMANDS["help"][1])

laplace_cdf = lambda L: lambda M: lambda x: (
    0.5 * e ** ((x - M) / L) if x < M else 1.0 - 0.5 / e ** ((x - M) / L)
)

# scales values between 0 and maximal allowed message length in telegram
scaler = lambda x: x / 4096
probability = laplace_cdf(scaler(config.long_message.max_len / 2))(
    scaler(config.long_message.max_len * 2)
)
is_long_message = (
    lambda m: len(m.text) > 100 and random() <= probability(scaler(len(m.text))) / 2.0
)

handle_cmd = lambda m: head(COMMANDS[cmd_name(m)])(m)

handler = lambda func, commands=None, content_types=None: {
    "func": chat_ok(func),
    "commands": commands,
    "content_types": content_types,
}

handlers = filter_modules(
    {
        "core": {
            handle_cmd: handler(cmd_ok, commands=list(COMMANDS.keys())),
            handle_unknown: handler(cmd_no_ok),
        },
        "captcha": {
            handle_new_user: handler(
                lambda m: bool(getattr(m, "new_chat_members", None)),
                content_types=["new_chat_members"],
            ),
            handle_verify_captcha: handler(
                is_captcha_user, content_types=config.captcha_properties.content_types
            ),
        },
        "long_message": {
            handle_long(config.long_message.messages): handler(is_long_message)
        },
        "reply": {
            handle_text_to_text_to_target(
                config.triggerReplies.text_to_text_to_target
            ): handler(
                message_ok_and_equal(config.triggerReplies.text_to_text_to_target)
            ),
            handle_text_to_sticker(config.triggerReplies.text_to_sticker): handler(
                message_ok(config.triggerReplies.text_to_sticker)
            ),
            handle_text_to_text(config.triggerReplies.text_to_text): handler(
                message_ok(config.triggerReplies.text_to_text)
            ),
            handle_stickers(config.triggerReplies.sticker_to_sticker): handler(
                sticker_ok(config.triggerReplies.sticker_to_sticker),
                content_types=["sticker"],
            ),
        },
    }
)

inline_handlers = {
    handle_inline_help(COMMANDS): {
        lambda query: query.query == "" and not is_captcha_user(query)
    }
}

query_check_data = lambda d: lambda c: chat_ok(c.message) and c.data.startswith(d)
query_handlers = filter_modules(
    {
        "event": {
            handle_title_change_attempt: {
                "func": lambda c: chat_ok(c.message) and validate_data(c)
            }
        },
        "captcha": {
            handle_captcha_button_press: {"func": query_check_data("captcha_")}
        },
    }
)

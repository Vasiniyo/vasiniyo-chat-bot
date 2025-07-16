from math import e
from random import random

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
from commands.text import handle_long, handle_text_to_sticker, handle_text_to_text
from config import (
    MESSAGE_MAX_LEN,
    allowed_chats,
    drinks,
    espers,
    long_message,
    phrases,
    sticker_to_sticker,
    text_to_sticker,
    text_to_text,
)
import safely_bot_utils as bot

from .fuzzy_match.fuzzy_match import choice_one_match

head = lambda l: l[0] if l else None
at = lambda l: lambda n: l[n] if n < len(l) else None

in_allowed_chat = lambda m: any(["*" in allowed_chats, str(m.chat.id) in allowed_chats])
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
sticker_ok = lambda t: lambda m: m.sticker.file_id in t.keys()
cmd_ok = lambda m: is_cmd_for_bot(split_cmd(m))
cmd_no_ok = lambda m: unknown_cmd(split_cmd(m))
is_captcha_user = lambda m: m.from_user.id in CAPTCHA_USERS

COMMANDS = {
    "help": (None, phrases("help_help")),
    "anime": (handle_anime, phrases("anime_help")),
    "top_espers": (handle_top_espers, phrases("top_espers_help")),
    "top_likes": (handle_top_likes, phrases("top_likes_help")),
    "like": (handle_like, phrases("like_help")),
    "rename": (prepare_game, phrases("rename_help")),
    "reg": (start, phrases("reg_help")),
    "drink_or_not": (handle_drink_or_not(drinks), phrases("drink_or_not_help")),
    "how_much_esper": (handle_how_much(espers), phrases("how_much_esper_help")),
    "players": (send_players, phrases("players_help")),
    "play": (play, phrases("play_help")),
}
COMMANDS["help"] = (handle_help(COMMANDS), COMMANDS["help"][1])

laplace_cdf = lambda L: lambda M: lambda x: (
    0.5 * e ** ((x - M) / L) if x < M else 1.0 - 0.5 / e ** ((x - M) / L)
)

# scales values between 0 and maximal allowed message length in telegram
scaler = lambda x: x / 4096
probability = laplace_cdf(scaler(MESSAGE_MAX_LEN / 2))(scaler(MESSAGE_MAX_LEN * 2))
is_long_message = lambda m: len(m.text) > 100 and random() <= probability(scaler(len(m.text))) / 2.0

handle_cmd = lambda m: head(COMMANDS[cmd_name(m)])(m)

handler = lambda func, commands=None, content_types=None: {
    "func": chat_ok(func),
    "commands": commands,
    "content_types": content_types,
}

handlers = {
    handle_cmd: handler(cmd_ok, commands=list(COMMANDS.keys())),
    handle_unknown: handler(cmd_no_ok),
    handle_long(long_message): handler(is_long_message),
    handle_text_to_sticker(text_to_sticker): handler(message_ok(text_to_sticker)),
    handle_text_to_text(text_to_text): handler(message_ok(text_to_text)),
    handle_stickers(sticker_to_sticker): handler(
        sticker_ok(sticker_to_sticker), content_types=["sticker"]
    ),
    handle_new_user: handler(
        lambda m: bool(getattr(m, "new_chat_members", None)),
        content_types=["new_chat_members"],
    ),
    handle_verify_captcha: handler(is_captcha_user),
}

inline_handlers = {handle_inline_help(COMMANDS): {lambda query: query.query == ""}}

query_handlers = {
    handle_title_change_attempt: {
        "func": lambda call: chat_ok(call.message) and call.data.startswith("number_")
    },
    handle_captcha_button_press: {
        "func": lambda call: chat_ok(call.message) and call.data.startswith("captcha_")
    },
}

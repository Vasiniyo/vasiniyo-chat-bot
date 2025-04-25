from captcha_manager import (
    CAPTCHA_USERS,
    handle_new_user,
    handle_user_left,
    handle_verify_captcha,
)
from commands.drink_or_not import handle_drink_or_not
from commands.event import play, send_players
from commands.help import handle_help, handle_inline_help, handle_unknown
from commands.how_much import handle_how_much
from commands.like import handle_like
from commands.roll_custom_title import handle_title_change_attempt, prepare_game, start
from commands.stickers import handle_stickers
from commands.text import handle_long, handle_text_to_sticker, handle_text_to_text
from commands.top import handle_top
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

COMMANDS = {
    "help": (None, phrases("help_help")),
    "top": (handle_top, phrases("top_help")),
    "like": (handle_like, phrases("like_help")),
    "rename": (prepare_game, phrases("rename_help")),
    "reg": (start, phrases("reg_help")),
    "drink_or_not": (handle_drink_or_not(drinks), phrases("drink_or_not_help")),
    "how_much_esper": (handle_how_much(espers), phrases("how_much_esper_help")),
    "players": (send_players, phrases("players_help")),
    "play": (play, phrases("play_help")),
}
COMMANDS["help"] = (handle_help(COMMANDS), COMMANDS["help"][1])

handle_cmd = lambda m: head(COMMANDS[cmd_name(m)])(m)
handlers = {
    handle_cmd: {"func": chat_ok(cmd_ok), "commands": list(COMMANDS.keys())},
    handle_unknown(phrases("unknown_command")): {"func": chat_ok(cmd_no_ok)},
    handle_long(long_message): {
        "func": chat_ok(lambda m: len(m.text) > MESSAGE_MAX_LEN)
    },
    handle_text_to_sticker(text_to_sticker): {
        "func": chat_ok(message_ok(text_to_sticker))
    },
    handle_text_to_text(text_to_text): {"func": chat_ok(message_ok(text_to_text))},
    handle_stickers(sticker_to_sticker): {
        "func": chat_ok(sticker_ok(sticker_to_sticker)),
        "content_types": ["sticker"],
    },
    handle_new_user: {
        "func": lambda m: bool(getattr(m, "new_chat_members", None)),
        "content_types": ["new_chat_members"],
    },
    handle_verify_captcha: {"func": lambda m: m.from_user.id in CAPTCHA_USERS},
}

inline_handlers = {handle_inline_help(COMMANDS): {lambda query: query.query == ""}}

query_handlers = {
    handle_title_change_attempt: {
        "func": lambda call: chat_ok(call.message) and call.data.startswith("number_")
    }
}

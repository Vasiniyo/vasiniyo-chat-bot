from captcha_manager import (
    CAPTCHA_USERS,
    handle_new_user,
    handle_user_left,
    handle_verify_captcha,
)
from commands.drink_or_not import handle_drink_or_not
from commands.help import handle_help, handle_inline_help, handle_unknown
from commands.like import handle_like
from commands.roll_custom_title import handle_title_change_attempt, prepare_game
from commands.stickers import handle_stickers
from commands.text import handle_long, handle_text_to_sticker, handle_text_to_text
from commands.top import handle_top
from config import MESSAGE_MAX_LEN, allowed_chats, bot, templates

from .fuzzy_match.fuzzy_match import test_match

head = lambda l: l[0] if l else None
at = lambda l: lambda n: l[n] if n < len(l) else None

in_allowed_chat = lambda m: any(["*" in allowed_chats, str(m.chat.id) in allowed_chats])
cmd_name = lambda m: head(split_cmd(m))
split_cmd = lambda m: head(m.text.lstrip("/").split()).split("@")
is_cmd_for_bot = lambda c: any([at(c)(1) is None, is_bot_username(c)])
is_bot_username = lambda c: at(c)(1) == bot.get_me().username
unknown_cmd = lambda c: all([is_bot_username(c), head(c) not in list(COMMANDS.keys())])

chat_ok = lambda p: lambda m: p(m) and in_allowed_chat(m)
message_ok = lambda c: lambda m: head(test_match(m.text, list(templates[c].keys())))
sticker_ok = lambda c: lambda m: m.sticker.file_id in templates[c]
cmd_ok = lambda m: is_cmd_for_bot(split_cmd(m))
cmd_no_ok = lambda m: unknown_cmd(split_cmd(m))

COMMANDS = {
    "help": (handle_help, "Выводит список доступных команд и их описание."),
    "top": (handle_top, "Показывает топ пользователей по лайкам."),
    "like": (handle_like, "Ставит лайк сообщению, на которое вы ответили."),
    "rename": (prepare_game, "Ставит случайную лычку."),
    "drink_or_not": (handle_drink_or_not, "Говорит пить сегодня или нет."),
}

handle_cmd = lambda m: head(COMMANDS[cmd_name(m)])(m)
handlers = {
    handle_cmd: {"func": chat_ok(cmd_ok), "commands": list(COMMANDS.keys())},
    handle_unknown: {"func": chat_ok(cmd_no_ok)},
    handle_long(templates["long_message"]): {
        "func": chat_ok(lambda m: len(m.text) > MESSAGE_MAX_LEN)
    },
    handle_text_to_sticker(templates["text_to_sticker"]): {
        "func": chat_ok(message_ok("text_to_sticker"))
    },
    handle_text_to_text(templates["text_to_text"]): {
        "func": chat_ok(message_ok("text_to_text"))
    },
    handle_stickers(templates["sticker_to_sticker"]): {
        "func": chat_ok(sticker_ok("sticker_to_sticker")),
        "content_types": ["sticker"],
    },
    handle_new_user: {
        "func": lambda m: bool(getattr(m, "new_chat_members", None)),
        "content_types": ["new_chat_members"],
    },
    handle_verify_captcha: {"func": lambda m: m.from_user.id in CAPTCHA_USERS},
    handle_long: {"func": chat_ok(lambda m: len(m.text) > MESSAGE_MAX_LEN)},
    handle_text_to_sticker: {"func": chat_ok(message_ok("text_to_sticker"))},
    handle_text_to_text: {"func": chat_ok(message_ok("text_to_text"))},
    handle_stickers: {"func": in_allowed_chat, "content_types": ["sticker"]},
}

inline_handlers = {handle_inline_help: {lambda query: query.query == ""}}

query_handlers = {
    handle_title_change_attempt: {
        "func": lambda call: chat_ok(call.message) and call.data.startswith("number_")
    }
}

from commands.help import handle_help, handle_unknown
from commands.like import handle_like
from commands.stickers import handle_stickers
from commands.text import handle_long, handle_text_to_sticker, handle_text_to_text
from commands.top import handle_top
from config import MESSAGE_MAX_LEN, allowed_chats

from .fuzzy_match.fuzzy_match import test_match


def in_allowed_chat(message):
    return "*" in allowed_chats or str(message.chat.id) in allowed_chats


def handle_command(message):
    command_text = message.text.lstrip("/")
    command_name = command_text.split()[0].split("@")[0]

    command_func, _ = COMMANDS.get(command_name, (None, None))
    if command_func:
        command_func(message)
    else:
        handle_unknown(message)


COMMANDS = {
    "help": (handle_help, "Выводит список доступных команд и их описание."),
    "top": (handle_top, "Показывает топ пользователей по лайкам."),
    "like": (handle_like, "Ставит лайк сообщению, на которое вы ответили."),
}

chat_ok = lambda p: lambda m: p(m) and in_allowed_chat(m)
message_ok = lambda c: lambda m: test_match(m.text, c)[0]

handlers = {
    handle_command: {"func": in_allowed_chat, "commands": list(COMMANDS.keys())},
    handle_long: {"func": chat_ok(lambda m: len(m.text) > MESSAGE_MAX_LEN)},
    handle_text_to_sticker: {"func": chat_ok(message_ok("text_to_sticker"))},
    handle_text_to_text: {"func": chat_ok(message_ok("text_to_text"))},
    handle_stickers: {"func": in_allowed_chat, "content_types": ["sticker"]},
}

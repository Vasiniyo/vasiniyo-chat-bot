from commands.help import handle_help
from commands.like import handle_like
from commands.top import handle_top

COMMANDS = {
    "help": (handle_help, "Выводит список доступных команд и их описание."),
    "top": (handle_top, "Показывает топ пользователей по лайкам."),
    "like": (handle_like, "Ставит лайк сообщению, на которое вы ответили."),
}

from commands.like import handle_like
from commands.top import handle_top

COMMANDS = {
    "top": (handle_top, "Показывает топ пользователей по лайкам."),
    "like": (handle_like, "Ставит лайк сообщению, на которое вы ответили."),
}

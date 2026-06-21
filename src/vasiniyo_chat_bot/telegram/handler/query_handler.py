from typing import Callable

from telebot.types import CallbackQuery

from vasiniyo_chat_bot.telegram.filter import Filter


class QueryHandler:
    handler: Callable[[CallbackQuery], None]
    kwargs: dict

    def __init__(
        self,
        allowed_chats: list[str],
        handler: Callable[[CallbackQuery], None],
        validator: Filter[CallbackQuery],
    ) -> None:
        in_allowed_chat = Filter(
            lambda call: "*" in allowed_chats
            or str(call.message.chat.id) in allowed_chats
        )
        self.handler = handler
        self.kwargs = {"func": in_allowed_chat & validator}

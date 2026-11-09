from typing import Callable

from telebot.types import InlineQuery

from vasiniyo_chat_bot.module.dto import InlineQueryContext
from vasiniyo_chat_bot.safely_bot_utils import safe_wrapper


class InlineQueryHandler:
    handler: Callable[[InlineQuery], None]
    kwargs: dict

    def __init__(self, handler: Callable[[InlineQueryContext], None]) -> None:
        self.handler = self._to_handler(handler)
        self.kwargs = {"func": lambda q: q.query == ""}

    @staticmethod
    @safe_wrapper(default=None)
    def _to_handler(
        handler: Callable[[InlineQueryContext], None],
    ) -> Callable[[InlineQuery], None]:
        return lambda call: handler(
            InlineQueryContext(
                user_id=call.from_user.id, query=call.query, callback_id=call.id
            )
        )

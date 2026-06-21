from typing import Callable

from telebot.types import CallbackQuery

from vasiniyo_chat_bot.module.captcha.captcha_controller import CaptchaCallbackContext
from vasiniyo_chat_bot.safely_bot_utils import safe_wrapper
from vasiniyo_chat_bot.telegram.filter import Filter
from vasiniyo_chat_bot.telegram.handler.query_handler import QueryHandler
from vasiniyo_chat_bot.telegram.mapper.mapper import call_to_captcha_context


class CaptchaQueryHandler(QueryHandler):
    def __init__(
        self,
        allowed_chats: list[str],
        handler: Callable[[CaptchaCallbackContext], None],
        validator: Filter[CallbackQuery],
    ) -> None:
        super().__init__(allowed_chats, self._to_handler(handler), validator)

    @staticmethod
    @safe_wrapper(default=None)
    def _to_handler(
        handler: Callable[[CaptchaCallbackContext], None],
    ) -> Callable[[CallbackQuery], None]:
        return lambda call: handler(call_to_captcha_context(call))

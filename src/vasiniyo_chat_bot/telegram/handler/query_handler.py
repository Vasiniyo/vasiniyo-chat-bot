import logging
import threading
from typing import Callable

from telebot.types import CallbackQuery

from vasiniyo_chat_bot.module.dto import CallbackContext
from vasiniyo_chat_bot.module.dto import InlineCallbackContext
from vasiniyo_chat_bot.safely_bot_utils import safe_wrapper
from vasiniyo_chat_bot.telegram.filter import Filter
from vasiniyo_chat_bot.telegram.mapper.mapper import call_to_callback_context
from vasiniyo_chat_bot.telegram.mapper.mapper import call_to_inline_callback_context

_logger = logging.getLogger(__name__)


class QueryHandler:
    _lock = threading.Lock()
    _pending: set[tuple[int, int]] = set()

    handler: Callable[[CallbackQuery], None]
    kwargs: dict

    def __init__(
        self,
        allowed_chats: list[str],
        handler: Callable[[CallbackContext | InlineCallbackContext], None],
        validator: Filter[CallbackQuery],
    ) -> None:
        in_allowed_chat = Filter(
            lambda call: "*" in allowed_chats
            or not hasattr(call.message, "chat")
            or str(call.message.chat.id) in allowed_chats
        )
        self.handler = self._to_handler(handler)
        self.kwargs = {"func": in_allowed_chat & validator}

    @safe_wrapper(default=None)
    def _to_handler(
        self, handler: Callable[[CallbackContext | InlineCallbackContext], None]
    ) -> Callable[[CallbackQuery], None]:
        def handle(call: CallbackQuery):
            ctx = call_to_callback_context(call) or call_to_inline_callback_context(
                call
            )
            if not ctx:
                return
            pending_key = (ctx.chat_id, ctx.user_id)
            with self._lock:
                if not ctx or pending_key in self._pending:
                    _logger.warning("fast_click", extra={"tg_call": call})
                    return
                self._pending.add(pending_key)
            try:
                handler(ctx)
            finally:
                self._pending.remove(pending_key)

        return handle

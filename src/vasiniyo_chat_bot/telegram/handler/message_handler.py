import logging
from typing import Any
from typing import Callable

from telebot.types import Message

from vasiniyo_chat_bot.module.dto import MessageContext
from vasiniyo_chat_bot.safely_bot_utils import safe_wrapper
from vasiniyo_chat_bot.telegram.filter import Filter
from vasiniyo_chat_bot.telegram.mapper.mapper import message_to_context

_logger = logging.getLogger(__name__)


class MessageHandler:
    handler: Callable[[Message], None]
    kwargs: dict[str, Any]

    def __init__(
        self,
        allowed_chats: list[str],
        handler: Callable[[MessageContext], None],
        validator: Filter[Message] = Filter(lambda _: True),
        content_types: list[str] | None = None,
    ) -> None:
        in_allowed_chat = Filter(
            lambda m: "*" in allowed_chats or str(m.chat.id) in allowed_chats
        )
        self.handler = self._to_handler(handler)
        self.kwargs = {
            "func": in_allowed_chat & validator,
            "content_types": content_types,
        }

    @staticmethod
    @safe_wrapper(default=None)
    def _to_handler(
        handler: Callable[[MessageContext], None],
    ) -> Callable[[Message], None]:
        def handle(message: Message):
            users = message.new_chat_members or [message.from_user]
            for user in users:
                if user.is_bot:
                    _logger.info(
                        "new_chat_members",
                        extra={"user_id": user.id, "details": "user is bot, skipping"},
                    )
                    continue
                if ctx := message_to_context(message):
                    handler(ctx)

        return handle

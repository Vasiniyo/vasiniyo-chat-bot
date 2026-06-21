import logging
from typing import Callable

from telebot.types import Message

from vasiniyo_chat_bot.module.dto import MessageContext
from vasiniyo_chat_bot.safely_bot_utils import safe_wrapper
from vasiniyo_chat_bot.telegram.filter import Filter
from vasiniyo_chat_bot.telegram.mapper.mapper import message_to_context

logger = logging.getLogger(__name__)


class MessageHandler:
    handler: Callable[[Message], None]
    kwargs: dict[str, any]

    def __init__(
        self,
        allowed_chats: list[str],
        handler: Callable[[MessageContext], None],
        validator: Filter[Message] = None,
        content_types: list[str] = None,
    ) -> None:
        in_allowed_chat = Filter(
            lambda m: "*" in allowed_chats or str(m.chat.id) in allowed_chats
        )
        self.handler = self._to_handler(handler)
        self.kwargs = {
            "func": in_allowed_chat & (validator or Filter(lambda _: True)),
            "content_types": list(content_types or []) or None,
        }

    @staticmethod
    @safe_wrapper(default=None)
    def _to_handler(
        handler: Callable[[MessageContext], None],
    ) -> Callable[[Message], None]:
        def inner(message: Message):
            users = message.new_chat_members or [message.from_user]
            for user in users:
                if user.is_bot:
                    logger.info(
                        "new_chat_members",
                        extra={"user_id": user.id, "details": "user is bot, skipping"},
                    )
                    continue
                handler(message_to_context(message))

        return inner

from typing import Callable

from telebot.types import Message

from vasiniyo_chat_bot.module.dto import MessageContext
from vasiniyo_chat_bot.telegram.filter import Filter
from vasiniyo_chat_bot.telegram.handler.message_handler import MessageHandler


class StickerHandler(MessageHandler):
    def __init__(
        self,
        allowed_chats: list[str],
        handler: Callable[[MessageContext], None],
        validator: Filter[Message] = None,
    ) -> None:
        super().__init__(allowed_chats, handler, validator, ["sticker"])

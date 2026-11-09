from typing import Callable

from vasiniyo_chat_bot.module.dto import MessageContext
from vasiniyo_chat_bot.telegram.handler.message_handler import MessageHandler


class StickerHandler(MessageHandler):
    def __init__(
        self, allowed_chats: list[str], handler: Callable[[MessageContext], None]
    ) -> None:
        super().__init__(allowed_chats, handler, content_types=["sticker"])

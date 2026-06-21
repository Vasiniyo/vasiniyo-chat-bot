from vasiniyo_chat_bot.module.reply.reply_controller import ReplyController
from vasiniyo_chat_bot.telegram.feature.feature import Feature
from vasiniyo_chat_bot.telegram.handler.message_handler import MessageHandler
from vasiniyo_chat_bot.telegram.handler.sticker_handler import StickerHandler


class ReplyFeature(Feature):
    def __init__(
        self, bot_username: str, allowed_chats: list[str], controller: ReplyController
    ) -> None:
        self._controller = controller
        super().__init__(
            bot_username,
            allowed_chats,
            message_handlers=self._message_handlers(allowed_chats),
        )

    def _message_handlers(self, allowed_chats: list[str]) -> list[MessageHandler]:
        if not self._controller:
            return []
        return [
            StickerHandler(allowed_chats, self._controller.handle_sticker_reply),
            MessageHandler(allowed_chats, self._controller.handle_text_reply),
        ]

from injector import inject

from vasiniyo_chat_bot.config.dto import BotSettings
from vasiniyo_chat_bot.module.reply.reply_controller import ReplyController
from vasiniyo_chat_bot.telegram.bot_service import BotService
from vasiniyo_chat_bot.telegram.feature.feature import Feature
from vasiniyo_chat_bot.telegram.handler.message_handler import MessageHandler
from vasiniyo_chat_bot.telegram.handler.sticker_handler import StickerHandler


@inject
class ReplyFeature(Feature):
    def __init__(
        self,
        settings: BotSettings,
        bot_service: BotService,
        controller: ReplyController,
    ) -> None:
        self._controller = controller
        super().__init__(
            settings,
            bot_service,
            message_handlers=self._message_handlers(settings.allowed_chats),
        )

    def _message_handlers(self, allowed_chats: list[str]) -> list[MessageHandler]:
        if not self._controller:
            return []
        return [
            StickerHandler(allowed_chats, self._controller.handle_sticker_reply),
            MessageHandler(allowed_chats, self._controller.handle_text_reply),
        ]

from vasiniyo_chat_bot.module.reply.dto import StickerResult, TextResult
from vasiniyo_chat_bot.telegram.bot_service import BotService


class ReplyRenderer:
    def __init__(self, bot_service: BotService):
        self.bot_service = bot_service

    def send_text(self, result: TextResult, chat_id: int, message_id: int):
        self.bot_service.send_message(result.text, chat_id, message_id)

    def send_sticker(self, sticker: StickerResult, chat_id: int, message_id: int):
        self.bot_service.send_sticker(sticker.file_id, chat_id, message_id)

from telebot.types import Message

from vasiniyo_chat_bot.module.reply.dto import StickerResult, TextResult
from vasiniyo_chat_bot.module.reply.reply_service import ReplyService
from vasiniyo_chat_bot.telegram.renderer.reply_renderer import ReplyRenderer


class ReplyController:
    def __init__(self, reply_service: ReplyService, reply_renderer: ReplyRenderer):
        self.reply_service = reply_service
        self.reply_renderer = reply_renderer

    def handle_text_reply(self, message: Message):
        result = self.reply_service.handle_text_replies(message.text)
        if isinstance(result, TextResult):
            message_id = (
                message.reply_to_message.id
                if result.to_reply and message.reply_to_message
                else message.id
            )
            self.reply_renderer.send_text(result, message.chat.id, message_id)
        elif isinstance(result, StickerResult):
            self.reply_renderer.send_sticker(result, message.chat.id, message.id)

    def handle_sticker_reply(self, message: Message):
        sticker = self.reply_service.handle_sticker_replies(message.sticker.file_id)
        if sticker:
            self.reply_renderer.send_sticker(sticker, message.chat.id, message.id)

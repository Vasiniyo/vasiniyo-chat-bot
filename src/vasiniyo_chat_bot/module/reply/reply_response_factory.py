from vasiniyo_chat_bot.module.dto import Response
from vasiniyo_chat_bot.module.reply.dto import StickerResult
from vasiniyo_chat_bot.module.reply.dto import TextResult


class ReplyResponseFactory:
    @staticmethod
    def text(result: TextResult) -> Response:
        return Response(result.text)

    @staticmethod
    def sticker(sticker: StickerResult) -> Response:
        return Response(sticker.file_id)

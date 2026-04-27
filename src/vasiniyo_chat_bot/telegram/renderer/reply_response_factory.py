from vasiniyo_chat_bot.module.reply.dto import StickerResult, TextResult
from vasiniyo_chat_bot.telegram.dto import Response


class ReplyResponseFactory:
    @staticmethod
    def text(result: TextResult) -> Response:
        return Response(result.text)

    @staticmethod
    def sticker(sticker: StickerResult) -> Response:
        return Response(sticker.file_id)

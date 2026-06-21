from vasiniyo_chat_bot.module.daily_size.dto import DailySizeResult
from vasiniyo_chat_bot.module.dto import Response


class DailySizeResponseFactory:
    @staticmethod
    def daily_size(size: DailySizeResult) -> Response:
        text = f"{size.label} у меня {size.daily_size}см {size.emoji}"
        return Response(text_units=text)

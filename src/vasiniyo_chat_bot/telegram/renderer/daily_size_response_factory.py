from vasiniyo_chat_bot.module.daily_size.dto import DailySizeResult
from vasiniyo_chat_bot.telegram.dto import Response


class DailySizeResponseFactory:
    @staticmethod
    def daily_size(size: DailySizeResult):
        text = f"{size.label} у меня {size.daily_size}см {size.emoji}"
        return Response(text_units=text)

from vasiniyo_chat_bot.module.drink_or_not.dto import DrinkAdvice
from vasiniyo_chat_bot.telegram.dto import Response


class DrinkResponseFactory:
    @staticmethod
    def advice(drink_advice: DrinkAdvice) -> Response:
        text = drink_advice.advice or "Решать тебе..."
        return Response(text)

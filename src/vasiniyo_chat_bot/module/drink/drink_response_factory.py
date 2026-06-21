from vasiniyo_chat_bot.module.drink.dto import DrinkAdvice
from vasiniyo_chat_bot.module.dto import Response


class DrinkResponseFactory:
    @staticmethod
    def advice(drink_advice: DrinkAdvice) -> Response:
        text = drink_advice.advice or "Решать тебе..."
        return Response(text)

import random

from vasiniyo_chat_bot.module.drink.dto import DrinkAdvice
from vasiniyo_chat_bot.module.drink.dto import Drinks


class DrinkService:
    def __init__(self, source: list[Drinks]):
        self._source = source

    def get_drink_advice(self, seed: int) -> DrinkAdvice:
        if self._source is None:
            return DrinkAdvice(advice=None)
        idx = seed % len(self._source)
        emoji = random.choice(self._source[idx].emoji) or ""
        answer = random.choice(self._source[idx].answer) or ""
        return DrinkAdvice(advice=" ".join(filter(None, (emoji, answer))) or None)

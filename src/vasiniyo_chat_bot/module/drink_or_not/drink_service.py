import random

from vasiniyo_chat_bot.module.drink_or_not.dto import DrinkAdvice, Drinks


class DrinkService:
    def __init__(self, source: list[Drinks]):
        self.source = source

    def get_drink_advice(self, seed: int) -> DrinkAdvice:
        if self.source is None:
            return DrinkAdvice(advice=None)
        idx = seed % len(self.source)
        emoji = random.choice(self.source[idx].emoji) or ""
        answer = random.choice(self.source[idx].answer) or ""
        return DrinkAdvice(advice=" ".join(filter(None, (emoji, answer))) or None)

from injector import inject

from vasiniyo_chat_bot.config.dto import Config
from vasiniyo_chat_bot.module.drink.dto import Drinks


@inject
class DrinksReader:
    def __init__(self, config: Config) -> None:
        self._config = config

    def load(self) -> list[Drinks]:
        return [
            Drinks(
                answer=sub.get("answer", ["Решение за тобой"]),
                emoji=sub.get("emoji", ["🤷‍♀️"]),
            )
            for sub in self._config.section.get("drink-or-not", {})
        ]

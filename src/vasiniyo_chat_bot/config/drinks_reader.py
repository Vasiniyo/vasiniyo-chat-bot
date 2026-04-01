from vasiniyo_chat_bot.module.drink_or_not.dto import Drinks


class DrinksReader:
    def __init__(self, section: dict[str, any]) -> None:
        self._section = section

    def load(self) -> list[Drinks]:
        return [
            Drinks(answer=sub.get("answer", []), emoji=sub.get("emoji", []))
            for sub in self._section.get("drink-or-not", {})
        ]

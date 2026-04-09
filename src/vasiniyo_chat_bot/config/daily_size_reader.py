from vasiniyo_chat_bot.module.daily_size.dto import DailySizeSettings


class DailySizeReader:
    def __init__(self, section: dict[str, any]) -> None:
        self._section = section

    def load(self) -> DailySizeSettings:
        sub = self._section.get("daily_size", {})
        return DailySizeSettings(
            labels=sub.get("labels", ["Морковка"]),
            sad_emoji=sub.get("sad_emoji", ["😭"]),
            happy_emoji=sub.get("happy_emoji", ["😏"]),
        )

from injector import inject

from vasiniyo_chat_bot.config.dto import Config
from vasiniyo_chat_bot.module.daily_size.dto import DailySizeSettings


@inject
class DailySizeReader:
    def __init__(self, config: Config) -> None:
        self._config = config

    def load(self) -> DailySizeSettings:
        sub = self._config.section.get("daily_size", {})
        return DailySizeSettings(
            labels=sub.get("labels", ["Морковка"]),
            sad_emoji=sub.get("sad_emoji", ["😭"]),
            happy_emoji=sub.get("happy_emoji", ["😏"]),
        )

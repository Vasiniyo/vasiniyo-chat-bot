import random

from vasiniyo_chat_bot.module.daily_size.dto import DailySizeResult
from vasiniyo_chat_bot.module.daily_size.dto import DailySizeSettings


class DailySizeService:
    def __init__(self, settings: DailySizeSettings):
        self._settings = settings

    def get_daily_size(self, seed: int) -> DailySizeResult:
        daily_size = random.Random(seed).randint(1, 40)
        if daily_size > 10:
            emoji = random.choice(self._settings.happy_emoji)
        else:
            emoji = random.choice(self._settings.sad_emoji)
        return DailySizeResult(
            label=random.choice(self._settings.labels),
            daily_size=daily_size,
            emoji=emoji,
        )

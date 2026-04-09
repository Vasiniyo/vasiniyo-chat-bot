from typing import Callable

from vasiniyo_chat_bot.module.daily_size.dto import DailySizeResult
from vasiniyo_chat_bot.telegram.bot_service import BotService


class DailySizeRenderer:
    def __init__(self, bot_service: BotService):
        self._bot_service = bot_service

    def send(self, get_content: Callable[[], DailySizeResult], query_id: str):
        def generate_answer():
            result = get_content()
            return f"{result.label} у меня {result.daily_size}см {result.emoji}"

        self._bot_service.answer_inline_query(
            [("Не стыдись и поделись", lambda: generate_answer())], query_id
        )

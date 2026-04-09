from telebot.types import InlineQuery

from vasiniyo_chat_bot.module.daily_size.daily_size_service import DailySizeService
from vasiniyo_chat_bot.module.daily_size.dto import DailySizeResult
from vasiniyo_chat_bot.safely_bot_utils import daily_hash
from vasiniyo_chat_bot.telegram.renderer.daily_size_renderer import DailySizeRenderer


class DailySizeController:
    def __init__(
        self,
        daily_size_service: DailySizeService,
        daily_size_renderer: DailySizeRenderer,
    ):
        self.daily_size_service = daily_size_service
        self.daily_size_renderer = daily_size_renderer

    def get_daily_size(self, inline_query: InlineQuery):
        def get_content() -> DailySizeResult:
            seed = daily_hash(inline_query.from_user.id)
            return self.daily_size_service.get_daily_size(seed)

        self.daily_size_renderer.send(get_content, inline_query.id)

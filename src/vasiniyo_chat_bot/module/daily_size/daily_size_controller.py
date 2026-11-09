from typing import Callable

from injector import inject

from vasiniyo_chat_bot.module.daily_size.daily_size_response_factory import (
    DailySizeResponseFactory,
)
from vasiniyo_chat_bot.module.daily_size.daily_size_service import DailySizeService
from vasiniyo_chat_bot.module.dto import InlineQueryContext
from vasiniyo_chat_bot.module.dto import Response
from vasiniyo_chat_bot.safely_bot_utils import daily_hash


@inject
class DailySizeController:
    def __init__(
        self,
        daily_size_service: DailySizeService,
        response_factory: DailySizeResponseFactory,
    ):
        self._daily_size_service = daily_size_service
        self._daily_size_response_factory = response_factory

    def get_daily_size(self, ctx: InlineQueryContext) -> Callable[[], Response]:
        return lambda: self._get_size(ctx)

    def _get_size(self, ctx: InlineQueryContext) -> Response:
        seed = daily_hash(ctx.user_id)
        size = self._daily_size_service.get_daily_size(seed)
        return self._daily_size_response_factory.daily_size(size)

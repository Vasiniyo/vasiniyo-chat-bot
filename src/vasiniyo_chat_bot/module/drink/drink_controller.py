from typing import Callable

from injector import inject

from vasiniyo_chat_bot.module.drink.drink_response_factory import DrinkResponseFactory
from vasiniyo_chat_bot.module.drink.drink_service import DrinkService
from vasiniyo_chat_bot.module.dto import InlineQueryContext
from vasiniyo_chat_bot.module.dto import Response
from vasiniyo_chat_bot.safely_bot_utils import daily_hash


@inject
class DrinkController:
    def __init__(
        self, drink_service: DrinkService, response_factory: DrinkResponseFactory
    ):
        self._drink_service = drink_service
        self._response_factory = response_factory

    def advice_drink(self, ctx: InlineQueryContext) -> Callable[[], Response]:
        return lambda: self._get_drink(ctx)

    def _get_drink(self, ctx: InlineQueryContext) -> Response:
        seed = daily_hash(ctx.user_id)
        drink_advice = self._drink_service.get_drink_advice(seed)
        return self._response_factory.advice(drink_advice)

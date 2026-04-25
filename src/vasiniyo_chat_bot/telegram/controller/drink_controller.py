from vasiniyo_chat_bot.module.drink_or_not.drink_service import DrinkService
from vasiniyo_chat_bot.safely_bot_utils import daily_hash
from vasiniyo_chat_bot.telegram.dto import UserContext
from vasiniyo_chat_bot.telegram.renderer.drink_response_factory import (
    DrinkResponseFactory,
)
from vasiniyo_chat_bot.telegram.renderer.renderer import Renderer


class DrinkController:
    def __init__(
        self,
        drink_service: DrinkService,
        response_factory: DrinkResponseFactory,
        renderer: Renderer,
    ):
        self._drink_service = drink_service
        self._response_factory = response_factory
        self._renderer = renderer

    def advice_drink(self, ctx: UserContext):
        seed = daily_hash(ctx.user_id)
        drink_advice = self._drink_service.get_drink_advice(seed)
        response = self._response_factory.advice(drink_advice)
        self._renderer.send(response, ctx)

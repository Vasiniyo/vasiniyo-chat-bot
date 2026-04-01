from telebot.types import Message

from vasiniyo_chat_bot.module.drink_or_not.drink_service import DrinkService
from vasiniyo_chat_bot.safely_bot_utils import daily_hash
from vasiniyo_chat_bot.telegram.renderer.drink_renderer import DrinkRenderer


class DrinkController:
    def __init__(self, drink_service: DrinkService, drink_renderer: DrinkRenderer):
        self.drink_service = drink_service
        self.drink_renderer = drink_renderer

    def advice_drink(self, message: Message):
        seed = daily_hash(message.from_user.id)
        drink_advice = self.drink_service.get_drink_advice(seed)
        self.drink_renderer.send(drink_advice, message.chat.id, message.id)

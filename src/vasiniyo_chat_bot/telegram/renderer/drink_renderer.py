from vasiniyo_chat_bot.module.drink_or_not.dto import DrinkAdvice
from vasiniyo_chat_bot.telegram.bot_service import BotService


class DrinkRenderer:
    def __init__(self, bot_service: BotService):
        self.bot_service = bot_service

    def send(self, drink_advice: DrinkAdvice, chat_id: int, message_id: int):
        if not drink_advice.advice:
            self.bot_service.send_message("Решать тебе...", chat_id, message_id)
        else:
            self.bot_service.send_message(drink_advice.advice, chat_id, message_id)

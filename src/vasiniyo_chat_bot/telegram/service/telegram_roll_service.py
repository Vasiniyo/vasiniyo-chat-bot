import random

from vasiniyo_chat_bot.module.dto import UserContext
from vasiniyo_chat_bot.module.titles.dice_service import DiceService
from vasiniyo_chat_bot.telegram.bot_service import BotService


class TelegramDiceService(DiceService):
    _dices = {
        "⚽": {"weight": 25, "win_values": (3, 4, 5)},
        "🏀": {"weight": 25, "win_values": (4, 5)},
        "🎯": {"weight": 54, "win_values": (6,)},
        "🎳": {"weight": 54, "win_values": (6,)},
        "🎰": {"weight": 112, "win_values": (1, 22, 43, 64)},
    }

    def __init__(self, bot_service: BotService):
        self._client = bot_service
        self._dice_keys = list(self._dices.keys())
        self._dice_weights = [self._dices[item]["weight"] for item in self._dice_keys]

    def roll_match(self, expected_value: int, ctx: UserContext) -> bool:
        self._client.clear_markup(ctx)
        dice_message = self._client.send_dice("🎲", ctx)
        return dice_message.dice.value == expected_value

    def roll_random(self, ctx: UserContext) -> bool:
        emoji = random.choices(self._dice_keys, weights=self._dice_weights)[0]
        self._client.clear_markup(ctx)
        dice_message = self._client.send_dice(emoji, ctx)
        win_values = self._dices[dice_message.dice.emoji]["win_values"]
        return dice_message.dice.value in win_values

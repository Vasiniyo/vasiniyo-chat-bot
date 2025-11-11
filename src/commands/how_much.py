import random

from config import Config
import safely_bot_utils as bot

daily_percentage = lambda user: bot.daily_hash(user.id) % 101


def handle_how_much(source: list[Config.Espers]):
    def _handle(message):
        percentage = daily_percentage(message.from_user)
        idx = min(len(source) - 1, percentage // (100 // len(source)))
        emoji = random.choice(source[idx].emoji)
        answer = random.choice(source[idx].answer)
        bot.reply_to(f"{emoji}\n[{percentage}%] {answer}")(message)

    return _handle

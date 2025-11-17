import random

from config import Config
import safely_bot_utils as bot


def handle_drink_or_not(source: list[Config.Drinks]):
    def _handle(message):
        idx = bot.daily_hash(message.from_user.id) % len(source)
        emoji = random.choice(source[idx].emoji)
        answer = random.choice(source[idx].answer)
        return bot.reply_to(f"{emoji} {answer}")(message)

    return _handle

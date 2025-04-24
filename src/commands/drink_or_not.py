import datetime
import random

from config import drinks
import safely_bot_utils as bot


def handle_drink_or_not(message):
    idx = (message.from_user.id + hash(datetime.date.today().toordinal())) % len(drinks)
    emoji = random.choice(drinks[idx].get("emoji"))
    answer = random.choice(drinks[idx].get("answer"))
    bot.reply_to(f"{emoji} {answer}")(message)

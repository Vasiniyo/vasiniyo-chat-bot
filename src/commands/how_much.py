import datetime
import random

import safely_bot_utils as bot


def handle_how_much(source):
    def _handle(message):
        user_id = message.from_user.id
        percentage = (user_id + hash(datetime.date.today().toordinal())) % 101
        idx = min(len(source) - 1, percentage // (100 // len(source)))
        emoji = random.choice(source[idx].get("emoji"))
        answer = random.choice(source[idx].get("answer"))
        bot.reply_to(f"{emoji}\n[{percentage}%] {answer}")(message)

    return _handle

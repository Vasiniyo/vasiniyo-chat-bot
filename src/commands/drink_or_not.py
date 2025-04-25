import datetime
import random

import safely_bot_utils as bot


def handle_drink_or_not(source):
    def _handle(message):
        idx = (message.from_user.id + hash(datetime.date.today().toordinal())) % len(
            source
        )
        emoji = random.choice(source[idx].get("emoji"))
        answer = random.choice(source[idx].get("answer"))
        return bot.reply_to(f"{emoji} {answer}")(message)

    return _handle

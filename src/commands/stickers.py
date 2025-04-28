import random

import safely_bot_utils as bot


def handle_stickers(answers):
    return lambda m: bot.send_sticker(random.choice(answers.get(m.sticker.file_id)))(m)

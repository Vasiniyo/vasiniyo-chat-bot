import random

import safely_bot_utils as bot


def handle_stickers(answers):
    def _handle(message):
        bot.send_sticker(random.choice(answers.get(message.sticker.file_id)))(message)

    return _handle

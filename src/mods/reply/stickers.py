import random

from commands.utils import handler
from config import sticker_to_sticker
import safely_bot_utils as bot

from ..register import reg_handler

sticker_ok = lambda t: lambda m: m.sticker.file_id in t.keys()
__handler = handler(sticker_ok(sticker_to_sticker), content_types=["sticker"])


# ========== HANDLERS =========================================================


@reg_handler(__handler, sticker_to_sticker)
def handle_stickers(answers):
    return lambda m: bot.send_sticker(random.choice(answers.get(m.sticker.file_id)))(m)


# reg_handler(handler(sticker_ok(sticker_to_sticker), content_types=["sticker"]))(handle_stickers(sticker_to_sticker))

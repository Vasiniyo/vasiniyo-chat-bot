import logging
import random

from commands.dispatcher import COMMANDS
from commands.stickers import handle_stickers
from commands.text import handle_text
from config import bot, templates

logger = logging.getLogger(__name__)


@bot.message_handler(commands=list(COMMANDS.keys()))
def handle_command(message):
    command_name = message.text.lstrip("/").split()[0]
    command_func, _ = COMMANDS.get(command_name, (None, None))
    if command_func:
        command_func(message)


bot.message_handler(func=lambda m: True)(handle_text)
bot.message_handler(content_types=["sticker"])(handle_stickers)

if __name__ == "__main__":
    logger.info("Bot started")
    bot.polling()

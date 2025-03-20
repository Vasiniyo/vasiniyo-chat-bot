import logging

from commands.dispatcher import COMMANDS
from commands.help import handle_unknown
from commands.stickers import handle_stickers
from commands.text import handle_text
from config import bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@bot.message_handler(commands=list(COMMANDS.keys()))
def handle_command(message):
    command_text = message.text.lstrip("/")
    command_name = command_text.split()[0].split("@")[0]
    logger.info(
        "Получена команда /%s от пользователя %s", command_name, message.from_user.id
    )

    command_func, _ = COMMANDS.get(command_name, (None, None))
    if command_func:
        command_func(message)
    else:
        handle_unknown(message)


bot.message_handler(func=lambda m: True)(handle_text)
bot.message_handler(content_types=["sticker"])(handle_stickers)

if __name__ == "__main__":
    logger.info("Бот запущен")
    bot.delete_webhook(drop_pending_updates=True)
    bot.polling()

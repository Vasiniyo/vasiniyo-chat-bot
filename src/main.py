import logging

from telebot.types import BotCommand

from commands.dispatcher import COMMANDS, handlers, inline_handlers
from config import bot

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Bot started")
    for handler, args in handlers.items():
        bot.message_handler(**args)(handler)
    bot.set_my_commands([BotCommand(cmd, desc[1]) for cmd, desc in COMMANDS.items()])
    for handler, args in inline_handlers.items():
        bot.inline_handler(*args)(handler)
    bot.delete_webhook(drop_pending_updates=True)
    bot.polling()

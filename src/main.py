import logging

from commands.dispatcher import handlers
from commands.log_decorator import log_handler
from config import bot

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Bot started")
    for handler, args in handlers.items():
        bot.message_handler(**args)(log_handler(handler))
    bot.delete_webhook(drop_pending_updates=True)
    bot.polling()

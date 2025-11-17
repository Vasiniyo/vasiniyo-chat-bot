import logging
import os
import pprint
import sys

from telebot.types import BotCommand

from commands.dispatcher import COMMANDS, handlers, inline_handlers, query_handlers
from config import bot
from event_queue import start_ticking_if_needed

logger = logging.getLogger(__name__)

# Check for test mode
TEST_MODE = "--test" in sys.argv or os.environ.get("TEST_MODE", "").lower() == "true"

if __name__ == "__main__":
    mode_str = " in TEST MODE" if TEST_MODE else ""
    logger.info(f"Bot started{mode_str}")

    start_ticking_if_needed()

    for handler, args in handlers.items():
        bot.message_handler(**args)(handler)

    for handler, args in inline_handlers.items():
        logger.info(f"\n[MAIN]\n {handler}: {pprint.pprint(args)}")
        bot.inline_handler(*args)(handler)

    for handler, args in query_handlers.items():
        bot.callback_query_handler(**args)(handler)

    bot.set_my_commands([BotCommand(cmd, desc[1]) for cmd, desc in COMMANDS.items()])
    bot.delete_webhook(drop_pending_updates=True)

    while True:
        try:
            bot.polling()
        except Exception as e:
            logger.exception(e)

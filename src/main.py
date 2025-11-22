import logging
import os
import signal
import sys
import time

from requests.exceptions import RequestException
from telebot.types import BotCommand
from urllib3.exceptions import HTTPError

from commands.dispatcher import COMMANDS, handlers, inline_handlers, query_handlers
from config import bot
from custom_typing.typing import LogDetails
from event_queue import start_ticking_if_needed
from logger import json_logger

logger = logging.getLogger(__name__)

# Check for test mode
TEST_MODE = "--test" in sys.argv or os.environ.get("TEST_MODE", "").lower() == "true"


def sigint_handler(_, __):
    json_logger.log(logging.INFO, "stop_polling")
    sys.exit(0)


signal.signal(signal.SIGINT, sigint_handler)

if __name__ == "__main__":
    mode_str = " in TEST MODE" if TEST_MODE else ""
    logger.info(f"Bot started{mode_str}")

    start_ticking_if_needed()

    for handler, args in handlers.items():
        bot.message_handler(**args)(handler)

    for handler, args in inline_handlers.items():
        bot.inline_handler(*args)(handler)

    for handler, args in query_handlers.items():
        bot.callback_query_handler(**args)(handler)

    bot.set_my_commands([BotCommand(cmd, desc[1]) for cmd, desc in COMMANDS.items()])
    bot.delete_webhook(drop_pending_updates=True)

    while True:
        try:
            json_logger.log(logging.INFO, "start_polling")
            bot.polling()
        except KeyboardInterrupt:
            json_logger.info("Bot stopped by user")
            break
        except (RequestException, HTTPError) as e:
            sleep_time = 5
            json_logger.log(
                logging.ERROR,
                "network_error",
                extra={
                    "details": LogDetails(
                        details=f"{type(e).__name__}: retrying in {sleep_time}s"
                    )
                },
            )
            time.sleep(sleep_time)
        except Exception as e:
            json_logger.exception(e)
            time.sleep(5)

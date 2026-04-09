import logging
import os
import signal
import sys
import time

from requests.exceptions import RequestException
from telebot.types import BotCommand
from urllib3.exceptions import HTTPError

from vasiniyo_chat_bot.config.config import load_all
from vasiniyo_chat_bot.database.sqlite.repository.dto import SqliteDatabaseSettings
from vasiniyo_chat_bot.event_queue import start_ticking_if_needed
from vasiniyo_chat_bot.logger.logger import LogFormatter
from vasiniyo_chat_bot.migration import sqlite_migration
from vasiniyo_chat_bot.telegram.dispatcher import init_controller

logger = logging.getLogger(__name__)


def sigint_handler(_, __):
    logger.info("stop_polling")
    sys.exit(0)


def main():
    print(
        "  _   __         _      _           _______        __  ___       __ \n"
        " | | / /__ ____ (_)__  (_)_ _____  / ___/ /  ___ _/ /_/ _ )___  / /_\n"
        " | |/ / _ `(_-</ / _ \/ / // / _ \/ /__/ _ \/ _ `/ __/ _  / _ \/ __/\n"
        " |___/\_,_/___/_/_//_/_/\_, /\___/\___/_//_/\_,_/\__/____/\___/\__/ \n"
        "                       /___/                                        \n"
    )
    logger_handler = logging.StreamHandler(sys.stdout)
    logger_handler.setFormatter(LogFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[logger_handler])
    signal.signal(signal.SIGINT, sigint_handler)
    start_ticking_if_needed()
    config_path = os.environ.get("CONFIG_PATH")
    config_ = load_all(config_path)
    if isinstance(config_.database, SqliteDatabaseSettings):
        sqlite_migration.apply_migrations(config_.database.database_path)
    bot = config_.bot_settings.bot
    controller = init_controller(config_)
    for handler in controller.messages:
        bot.message_handler(**handler.kwargs)(handler.handler)
    for handler in controller.callbacks:
        bot.callback_query_handler(**handler.kwargs)(handler.handler)
    if inline_handler := controller.inline:
        bot.inline_handler(**inline_handler.kwargs)(inline_handler.handler)
    bot.set_my_commands(
        [BotCommand(title, desc) for title, desc in controller.my_commands.items()]
    )
    logger.info(
        "commands_enabled", extra={"commands": list(controller.my_commands.keys())}
    )
    bot.delete_webhook(drop_pending_updates=True)
    if "test" in config_.bot_settings.mods:
        logger.info("test_mode_enabled")
    while True:
        try:
            logger.info("start_polling")
            bot.polling()
        except KeyboardInterrupt:
            logger.info("bot_stopped", extra={"reason": "Stopped by user"})
            break
        except (RequestException, HTTPError):
            sleep_time = 5
            logger.error(
                "bot_paused",
                extra={"reason": "Network error", "sleep_time": sleep_time},
            )
            time.sleep(sleep_time)
        except:
            sleep_time = 5
            logger.exception(
                "bot_paused",
                extra={"reason": "Unknown error", "sleep_time": sleep_time},
            )
            time.sleep(sleep_time)


if __name__ == "__main__":
    main()

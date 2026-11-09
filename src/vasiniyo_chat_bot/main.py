import logging
import signal
import sys
import time

from requests.exceptions import RequestException
from telebot import TeleBot
from telebot.types import BotCommand
from urllib3.exceptions import HTTPError

from vasiniyo_chat_bot.config.dto import BotSettings
from vasiniyo_chat_bot.di import container
from vasiniyo_chat_bot.event_queue import start_ticking_if_needed
from vasiniyo_chat_bot.logger.logger import LogFormatter
from vasiniyo_chat_bot.module.reply.dto import TriggerReplies
from vasiniyo_chat_bot.telegram.feature_registry import FeatureRegistry

_logger = logging.getLogger(__name__)


def sigint_handler(_, __):
    _logger.info("stop_polling")
    sys.exit(0)


def main():
    print(
        r"  _   __         _      _           _______        __  ___       __ ",
        r" | | / /__ ____ (_)__  (_)_ _____  / ___/ /  ___ _/ /_/ _ )___  / /_",
        r" | |/ / _ `(_-</ / _ \/ / // / _ \/ /__/ _ \/ _ `/ __/ _  / _ \/ __/",
        r" |___/\_,_/___/_/_//_/_/\_, /\___/\___/_//_/\_,_/\__/____/\___/\__/ ",
        r"                       /___/                                        ",
        sep="\n",
        end="\n",
    )
    logger_handler = logging.StreamHandler(sys.stdout)
    logger_handler.setFormatter(LogFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[logger_handler])
    signal.signal(signal.SIGINT, sigint_handler)
    start_ticking_if_needed()
    bot = container.get(TeleBot)
    registry = container.get(FeatureRegistry)
    for handler in registry.message_handlers():
        bot.message_handler(**handler.kwargs)(handler.handler)
    for handler in registry.callback_query_handlers():
        bot.callback_query_handler(**handler.kwargs)(handler.handler)
    if inline_handler := registry.inline_handler():
        bot.inline_handler(**inline_handler.kwargs)(inline_handler.handler)
    my_commands = registry.my_commands()
    bot.set_my_commands(
        [BotCommand(title, desc) for title, desc in my_commands.items()]
    )
    for mod in container.get(BotSettings).mods:
        _logger.info("module_enabled", extra={"mod": mod})
    for command in sorted(my_commands.keys()):
        _logger.info("command_enabled", extra={"command": command})
    for reply in container.get(TriggerReplies).text_replies:
        for response in reply.responses:
            _logger.info(
                f"reply_loaded",
                extra={
                    "response_type": reply.response_type.name,
                    "chance": reply.chance,
                    "to_target": reply.to_target,
                    "fuzzy": reply.fuzzy,
                    "request": reply.request,
                    "responses": response,
                },
            )
    for reply in container.get(TriggerReplies).sticker_replies:
        for response in reply.responses:
            _logger.info(
                f"reply_loaded",
                extra={
                    "response_type": reply.response_type.name,
                    "chance": reply.chance,
                    "to_target": reply.to_target,
                    "fuzzy": reply.fuzzy,
                    "request": reply.request,
                    "responses": response,
                },
            )
    bot.delete_webhook(drop_pending_updates=True)
    while True:
        try:
            _logger.info("start_polling")
            bot.polling()
        except KeyboardInterrupt:
            _logger.info("bot_stopped", extra={"reason": "Stopped by user"})
            break
        except (RequestException, HTTPError):
            sleep_time = 5
            _logger.error(
                "bot_paused",
                extra={"reason": "Network error", "sleep_time": sleep_time},
            )
            time.sleep(sleep_time)
        except:
            sleep_time = 5
            _logger.exception(
                "bot_paused",
                extra={"reason": "Unknown error", "sleep_time": sleep_time},
            )
            time.sleep(sleep_time)


if __name__ == "__main__":
    main()

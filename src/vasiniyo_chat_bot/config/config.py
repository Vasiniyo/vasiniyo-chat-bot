import logging

from telebot import TeleBot
from telebot.types import Sticker
import toml

from vasiniyo_chat_bot.config import (
    CustomTitlesReader,
    DrinksReader,
    EventReader,
    LongMessageReader,
    ReplyReader,
    StickersConfigReader,
)
from vasiniyo_chat_bot.config.bot_settings_reader import BotSettingsReader
from vasiniyo_chat_bot.config.captcha_reader import CaptchaReader
from vasiniyo_chat_bot.config.daily_size_reader import DailySizeReader
from vasiniyo_chat_bot.config.database_reader import DatabaseReader
from vasiniyo_chat_bot.config.dto import Config
from vasiniyo_chat_bot.safely_bot_utils import safe_wrapper

logger = logging.getLogger(__name__)


def load_all(path: str):
    toml_config = toml.load(path)
    bot_settings = BotSettingsReader(toml_config).load()
    packs = StickersConfigReader(toml_config).load_configuration()
    stickers_by_unique_id = {
        (pack, sticker.file_unique_id): sticker.file_id
        for pack in packs
        for sticker in _get_sticker_set(bot_settings.bot, pack)
    }
    return Config(
        trigger_replies=ReplyReader(toml_config, stickers_by_unique_id).load(),
        long_message=LongMessageReader(toml_config).load(),
        custom_titles=CustomTitlesReader(toml_config).load(),
        drinks=DrinksReader(toml_config).load(),
        daily_size_settings=DailySizeReader(toml_config).load(),
        captcha_properties=CaptchaReader(toml_config).load(),
        event=EventReader(toml_config).load(),
        bot_settings=bot_settings,
        database=DatabaseReader(toml_config).load(),
    )


@safe_wrapper(default=[], message="Failed to get sticker set")
def _get_sticker_set(bot: TeleBot, pack: str) -> list[Sticker]:
    logger.info("get_sticker_set", extra={"sticker_set": pack})
    return bot.get_sticker_set(pack).stickers

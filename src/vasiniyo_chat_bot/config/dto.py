from dataclasses import dataclass
from typing import Protocol

from vasiniyo_chat_bot.config.bot_settings_reader import BotSettings
from vasiniyo_chat_bot.module.captcha.dto import Captcha
from vasiniyo_chat_bot.module.daily_size.dto import DailySizeSettings
from vasiniyo_chat_bot.module.drink_or_not.dto import Drinks
from vasiniyo_chat_bot.module.play.dto import Event
from vasiniyo_chat_bot.module.reply.dto import LongMessage, TriggerReplies
from vasiniyo_chat_bot.module.titles.dto import CustomTitles


@dataclass(frozen=True)
class DatabaseSettings(Protocol): ...


@dataclass(frozen=True)
class Config:
    trigger_replies: TriggerReplies
    long_message: LongMessage
    custom_titles: CustomTitles
    drinks: list[Drinks]
    daily_size_settings: DailySizeSettings
    captcha_properties: Captcha
    event: Event
    bot_settings: BotSettings
    database: DatabaseSettings

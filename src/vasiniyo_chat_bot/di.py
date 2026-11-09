import logging
import os

from injector import Injector
from injector import Module
from injector import multiprovider
from injector import provider
from injector import singleton
from telebot import TeleBot
from telebot.types import Sticker
import toml

from vasiniyo_chat_bot.config.dto import BotSettings
from vasiniyo_chat_bot.config.dto import Config
from vasiniyo_chat_bot.config.reader.bot_settings_reader import BotSettingsReader
from vasiniyo_chat_bot.config.reader.captcha_reader import CaptchaReader
from vasiniyo_chat_bot.config.reader.custom_titles_reader import CustomTitlesReader
from vasiniyo_chat_bot.config.reader.daily_size_reader import DailySizeReader
from vasiniyo_chat_bot.config.reader.database_reader import DatabaseReader
from vasiniyo_chat_bot.config.reader.drinks_reader import DrinksReader
from vasiniyo_chat_bot.config.reader.event_reader import EventReader
from vasiniyo_chat_bot.config.reader.long_message_reader import LongMessageReader
from vasiniyo_chat_bot.config.reader.reply_reader import ReplyReader
from vasiniyo_chat_bot.config.reader.stickers_reader import StickersReader
from vasiniyo_chat_bot.database.database import Database
from vasiniyo_chat_bot.module.anime.provider.anilist_anime_provider import (
    AnilistAnimeProvider,
)
from vasiniyo_chat_bot.module.anime.provider.anime_provider import AnimeProvider
from vasiniyo_chat_bot.module.anime.provider.shikimori_anime_provider import (
    ShikimoriAnimeProvider,
)
from vasiniyo_chat_bot.module.captcha.dto import Captcha
from vasiniyo_chat_bot.module.daily_size.dto import DailySizeSettings
from vasiniyo_chat_bot.module.drink.dto import Drinks
from vasiniyo_chat_bot.module.play.dto import Event
from vasiniyo_chat_bot.module.play.event_player_service import EventPlayersService
from vasiniyo_chat_bot.module.renderer import Renderer
from vasiniyo_chat_bot.module.reply.dto import LongMessage
from vasiniyo_chat_bot.module.reply.dto import TriggerReplies
from vasiniyo_chat_bot.module.titles.dice_service import DiceService
from vasiniyo_chat_bot.module.titles.dto import CustomTitles
from vasiniyo_chat_bot.module.user_service import UserService
from vasiniyo_chat_bot.safely_bot_utils import safe_wrapper
from vasiniyo_chat_bot.telegram.service.telegram_event_players_service import (
    TelegramEventPlayersService,
)
from vasiniyo_chat_bot.telegram.service.telegram_roll_service import TelegramDiceService
from vasiniyo_chat_bot.telegram.service.telegram_user_service import TelegramUserService
from vasiniyo_chat_bot.telegram.telegram_renderer import TelegramRenderer

_logger = logging.getLogger(__name__)


class DiProvider(Module):
    @provider
    @singleton
    def provide_config(self) -> Config:
        config_path = os.environ.get("CONFIG_PATH")
        if not config_path:
            raise Exception("CONFIG_PATH not set")
        return Config(section=toml.load(config_path))

    @provider
    @singleton
    def provide_bot_settings(self, reader: BotSettingsReader) -> BotSettings:
        return reader.load()

    @provider
    @singleton
    def provide_database(self, reader: DatabaseReader) -> Database:
        return reader.load()

    @provider
    @singleton
    def provide_daily_size_settings(self, reader: DailySizeReader) -> DailySizeSettings:
        return reader.load()

    @provider
    @singleton
    def provide_captcha_properties(self, reader: CaptchaReader) -> Captcha:
        return reader.load()

    @provider
    @singleton
    def provide_custom_titles(self, reader: CustomTitlesReader) -> CustomTitles:
        return reader.load()

    @provider
    @singleton
    def provide_long_message(self, reader: LongMessageReader) -> LongMessage:
        return reader.load()

    @provider
    @singleton
    def provide_event(self, reader: EventReader) -> Event:
        return reader.load()

    @multiprovider
    @singleton
    def provide_drinks(self, reader: DrinksReader) -> list[Drinks]:
        return reader.load()

    @provider
    @singleton
    def provide_bot(self, settings: BotSettings) -> TeleBot:
        try:
            return TeleBot(settings.api_token)
        except Exception as e:
            _logger.error("BOT_API_TOKEN is invalid")
            raise e

    @provider
    @singleton
    def provide_anime_provider(self, renderer: TelegramRenderer) -> Renderer:
        return renderer

    @provider
    @singleton
    def provide_renderer(self) -> Renderer:
        return container.get(TelegramRenderer)

    @provider
    @singleton
    def provide_dice_service(self) -> DiceService:
        return container.get(TelegramDiceService)

    @provider
    @singleton
    def provide_user_service(self) -> UserService:
        return container.get(TelegramUserService)

    @provider
    @singleton
    def provide_event_players_service(self) -> EventPlayersService:
        return container.get(TelegramEventPlayersService)

    @multiprovider
    @singleton
    def provide_anime_providers(
        self,
        shikimori_anime_provider: ShikimoriAnimeProvider,
        anilist_anime_provider: AnilistAnimeProvider,
    ) -> list[AnimeProvider]:
        return [anilist_anime_provider, shikimori_anime_provider]

    @provider
    @singleton
    def provide_trigger_replies(
        self, config: Config, stickers_reader: StickersReader, bot: TeleBot
    ) -> TriggerReplies:
        packs = stickers_reader.load()
        stickers_by_unique_id = {
            (pack, sticker.file_unique_id): sticker.file_id
            for pack in packs
            for sticker in _get_sticker_set(bot, pack)
        }
        return ReplyReader(config, stickers_by_unique_id).load()


@safe_wrapper(default=[], message="Failed to get sticker set")
def _get_sticker_set(bot: TeleBot, pack: str) -> list[Sticker]:
    _logger.info("get_sticker_set", extra={"sticker_set": pack})
    return bot.get_sticker_set(pack).stickers


container = Injector([DiProvider()])

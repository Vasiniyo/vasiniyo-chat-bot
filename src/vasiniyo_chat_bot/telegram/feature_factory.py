from vasiniyo_chat_bot.anilist.anilist_anime_provider import AnilistAnimeProvider
from vasiniyo_chat_bot.config.dto import Config
from vasiniyo_chat_bot.database.sqlite.dao import EventsDao
from vasiniyo_chat_bot.database.sqlite.dao import LikesDao
from vasiniyo_chat_bot.database.sqlite.dao import TitlesBagDAO
from vasiniyo_chat_bot.database.sqlite.dao import TitlesStatesDAO
from vasiniyo_chat_bot.database.sqlite.repository.dto import SqliteDatabaseSettings
from vasiniyo_chat_bot.database.sqlite.repository.sqlite_events_repository import (
    SqliteEventsRepository,
)
from vasiniyo_chat_bot.database.sqlite.repository.sqlite_likes_repository import (
    SqliteLikesRepository,
)
from vasiniyo_chat_bot.database.sqlite.repository.sqlite_titles_repository import (
    SqliteTitlesRepository,
)
from vasiniyo_chat_bot.module.anime.anime_controller import AnimeController
from vasiniyo_chat_bot.module.anime.anime_payload_factory import AnimePayloadFactory
from vasiniyo_chat_bot.module.anime.anime_response_factory import AnimeResponseFactory
from vasiniyo_chat_bot.module.anime.anime_service import AnimeService
from vasiniyo_chat_bot.module.captcha.captcha_controller import CaptchaController
from vasiniyo_chat_bot.module.captcha.captcha_payload_factory import (
    CaptchaPayloadFactory,
)
from vasiniyo_chat_bot.module.captcha.captcha_repository import CaptchaRepository
from vasiniyo_chat_bot.module.captcha.captcha_response_factory import (
    CaptchaResponseFactory,
)
from vasiniyo_chat_bot.module.captcha.captcha_service import CaptchaService
from vasiniyo_chat_bot.module.daily_size.daily_size_controller import (
    DailySizeController,
)
from vasiniyo_chat_bot.module.daily_size.daily_size_response_factory import (
    DailySizeResponseFactory,
)
from vasiniyo_chat_bot.module.daily_size.daily_size_service import DailySizeService
from vasiniyo_chat_bot.module.drink.drink_controller import DrinkController
from vasiniyo_chat_bot.module.drink.drink_response_factory import DrinkResponseFactory
from vasiniyo_chat_bot.module.drink.drink_service import DrinkService
from vasiniyo_chat_bot.module.help.help_controller import HelpController
from vasiniyo_chat_bot.module.help.help_response_factory import HelpResponseFactory
from vasiniyo_chat_bot.module.like.like_controller import LikeController
from vasiniyo_chat_bot.module.like.like_response_factory import LikeResponseFactory
from vasiniyo_chat_bot.module.like.like_service import LikeService
from vasiniyo_chat_bot.module.play.image_service import ImageService
from vasiniyo_chat_bot.module.play.play_controller import PlayController
from vasiniyo_chat_bot.module.play.play_response_factory import PlayResponseFactory
from vasiniyo_chat_bot.module.play.play_service import PlayService
from vasiniyo_chat_bot.module.renderer import Renderer
from vasiniyo_chat_bot.module.reply.reply_controller import ReplyController
from vasiniyo_chat_bot.module.reply.reply_response_factory import ReplyResponseFactory
from vasiniyo_chat_bot.module.reply.reply_service import ReplyService
from vasiniyo_chat_bot.module.titles.titles_controller import TitlesController
from vasiniyo_chat_bot.module.titles.titles_payload_factory import TitlesPayloadFactory
from vasiniyo_chat_bot.module.titles.titles_provider import TitlesProvider
from vasiniyo_chat_bot.module.titles.titles_response_factory import (
    TitlesResponseFactory,
)
from vasiniyo_chat_bot.module.titles.titles_service import TitlesService
from vasiniyo_chat_bot.shikimori.shikimori_anime_provider import ShikimoriAnimeProvider
from vasiniyo_chat_bot.telegram.bot_service import BotService
from vasiniyo_chat_bot.telegram.feature.anime_feature import AnimeFeature
from vasiniyo_chat_bot.telegram.feature.captcha_feature import CaptchaFeature
from vasiniyo_chat_bot.telegram.feature.daily_size_feature import DailySizeFeature
from vasiniyo_chat_bot.telegram.feature.drink_feature import DrinkFeature
from vasiniyo_chat_bot.telegram.feature.feature import Feature
from vasiniyo_chat_bot.telegram.feature.help_feature import HelpFeature
from vasiniyo_chat_bot.telegram.feature.like_feature import LikeFeature
from vasiniyo_chat_bot.telegram.feature.play_feature import PlayFeature
from vasiniyo_chat_bot.telegram.feature.reply_feature import ReplyFeature
from vasiniyo_chat_bot.telegram.feature.titles_feature import TitlesFeature
from vasiniyo_chat_bot.telegram.keyboard.anime_keyboard_factory import (
    AnimeKeyboardFactory,
)
from vasiniyo_chat_bot.telegram.keyboard.captcha_keyboard_factory import (
    CaptchaKeyboardFactory,
)
from vasiniyo_chat_bot.telegram.keyboard.titles_keyboard_factory import (
    TitlesKeyboardFactory,
)
from vasiniyo_chat_bot.telegram.service.markdown_v2_service import MarkdownV2Service
from vasiniyo_chat_bot.telegram.service.telegram_event_players_service import (
    TelegramEventPlayersService,
)
from vasiniyo_chat_bot.telegram.service.telegram_roll_service import TelegramDiceService
from vasiniyo_chat_bot.telegram.service.telegram_user_service import TelegramUserService
from vasiniyo_chat_bot.telegram.telegram_renderer import TelegramRenderer


class FeatureFactory:
    renderer: Renderer

    def __init__(self, config: Config) -> None:
        self._config = config
        self._bot_service = BotService(config.bot_settings.bot, MarkdownV2Service())
        self._bot_username = self._bot_service.get_me().username
        self._user_service = TelegramUserService(self._bot_service)
        self.renderer = TelegramRenderer(
            self._bot_service,
            TitlesKeyboardFactory(TitlesPayloadFactory()),
            AnimeKeyboardFactory(AnimePayloadFactory()),
            CaptchaKeyboardFactory(CaptchaPayloadFactory()),
        )

    def daily_size_feature(self) -> Feature:
        return DailySizeFeature(
            self._bot_username,
            self._config.bot_settings.allowed_chats,
            DailySizeController(
                DailySizeService(self._config.daily_size_settings),
                DailySizeResponseFactory(),
                self.renderer,
            ),
            self._config.bot_settings.commands,
        )

    def captcha_feature(self) -> Feature:
        return CaptchaFeature(
            self._bot_username,
            self._config.bot_settings.allowed_chats,
            CaptchaController(
                self._user_service,
                CaptchaService(self._config.captcha_properties, CaptchaRepository()),
                CaptchaResponseFactory(self._config.captcha_properties),
                self.renderer,
            ),
            self._user_service,
        )

    def reply_feature(self) -> Feature:
        return ReplyFeature(
            self._bot_username,
            self._config.bot_settings.allowed_chats,
            ReplyController(
                ReplyService(self._config.long_message, self._config.trigger_replies),
                ReplyResponseFactory(),
                self.renderer,
            ),
        )

    def like_feature(self) -> Feature:
        return LikeFeature(
            self._bot_username,
            self._config.bot_settings.allowed_chats,
            LikeController(
                LikeService(
                    SqliteLikesRepository(LikesDao(), self._database_settings())
                ),
                LikeResponseFactory(),
                self.renderer,
            ),
            self._config.bot_settings.commands,
        )

    def drink_feature(self) -> Feature:
        return DrinkFeature(
            self._bot_username,
            self._config.bot_settings.allowed_chats,
            DrinkController(
                DrinkService(self._config.drinks), DrinkResponseFactory(), self.renderer
            ),
            self._config.bot_settings.commands,
        )

    def anime_feature(self) -> Feature:
        return AnimeFeature(
            self._bot_username,
            self._config.bot_settings.allowed_chats,
            AnimeController(
                AnimeService([AnilistAnimeProvider(), ShikimoriAnimeProvider()]),
                AnimeResponseFactory(),
                self.renderer,
            ),
            self._config.bot_settings.commands,
        )

    def titles_feature(self) -> Feature:
        return TitlesFeature(
            self._bot_username,
            self._config.bot_settings.allowed_chats,
            TitlesController(
                TitlesService(
                    TitlesProvider(self._config.custom_titles),
                    SqliteTitlesRepository(
                        TitlesStatesDAO(), TitlesBagDAO(), self._database_settings()
                    ),
                ),
                TelegramDiceService(self._bot_service),
                self._user_service,
                TitlesResponseFactory(),
                self.renderer,
            ),
            self._config.bot_settings.commands,
        )

    def play_feature(self) -> Feature:
        return PlayFeature(
            self._bot_username,
            self._config.bot_settings.allowed_chats,
            PlayController(
                PlayService(
                    TelegramEventPlayersService(self._bot_service),
                    SqliteEventsRepository(EventsDao(), self._database_settings()),
                    self._config.event.play_categories,
                ),
                PlayResponseFactory(
                    self._user_service,
                    ImageService(
                        self._config.event.default_winner_avatar,
                        self._config.event.winner_pictures,
                    ),
                ),
                self.renderer,
            ),
            self._config.bot_settings.commands,
        )

    def help_feature(self) -> Feature:
        return HelpFeature(
            self._bot_username,
            self._config.bot_settings.allowed_chats,
            HelpController(HelpResponseFactory(), self.renderer),
            self._config.bot_settings.commands,
        )

    def _database_settings(self) -> SqliteDatabaseSettings:
        settings = self._config.database
        if not isinstance(settings, SqliteDatabaseSettings):
            raise NotImplementedError(
                f"Database type {type(settings).__name__} is not supported yet"
            )
        return settings

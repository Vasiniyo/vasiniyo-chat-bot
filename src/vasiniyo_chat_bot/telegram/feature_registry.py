import logging

from injector import inject

from vasiniyo_chat_bot.config.dto import BotSettings
from vasiniyo_chat_bot.module.renderer import Renderer
from vasiniyo_chat_bot.telegram.feature.anime_feature import AnimeFeature
from vasiniyo_chat_bot.telegram.feature.captcha_feature import CaptchaFeature
from vasiniyo_chat_bot.telegram.feature.daily_size_feature import DailySizeFeature
from vasiniyo_chat_bot.telegram.feature.drink_feature import DrinkFeature
from vasiniyo_chat_bot.telegram.feature.help_feature import HelpFeature
from vasiniyo_chat_bot.telegram.feature.like_feature import LikeFeature
from vasiniyo_chat_bot.telegram.feature.play_feature import PlayFeature
from vasiniyo_chat_bot.telegram.feature.reply_feature import ReplyFeature
from vasiniyo_chat_bot.telegram.feature.titles_feature import TitlesFeature
from vasiniyo_chat_bot.telegram.handler.command_handler import CommandHandler
from vasiniyo_chat_bot.telegram.handler.inline_query_handler import InlineQueryHandler
from vasiniyo_chat_bot.telegram.handler.message_handler import MessageHandler
from vasiniyo_chat_bot.telegram.handler.query_handler import QueryHandler

_logger = logging.getLogger(__name__)


@inject
class FeatureRegistry:
    def __init__(
        self,
        captcha_feature: CaptchaFeature,
        help_feature: HelpFeature,
        like_feature: LikeFeature,
        drink_feature: DrinkFeature,
        anime_feature: AnimeFeature,
        titles_feature: TitlesFeature,
        play_feature: PlayFeature,
        reply_feature: ReplyFeature,
        daily_size_feature: DailySizeFeature,
        settings: BotSettings,
        renderer: Renderer,
    ):
        self._features = [
            feature
            for feature in [
                feature if mod in settings.mods else None
                for mod, feature in {
                    "captcha": captcha_feature,
                    "help": help_feature,
                    "like": like_feature,
                    "drink": drink_feature,
                    "anime": anime_feature,
                    "titles": titles_feature,
                    "play": play_feature,
                    "reply": reply_feature,
                    "daily_size": daily_size_feature,
                }.items()
            ]
            if feature is not None
        ]
        self._renderer = renderer

    def my_commands(self) -> dict[str, str]:
        commands = {
            key: command
            for feature in self._features
            for key, command in feature.commands().items()
        }
        return {
            command.info.name: command.info.description for command in commands.values()
        }

    def message_handlers(self) -> list[MessageHandler]:
        return [
            handler
            for _, handler in sorted(
                [
                    (feature, handler)
                    for feature in self._features
                    for handler in feature.messages()
                ],
                key=lambda item: (
                    not isinstance(item[0], CaptchaFeature),
                    not isinstance(item[1], CommandHandler),
                ),
            )
        ]

    def callback_query_handlers(self) -> list[QueryHandler]:
        return [
            handler for feature in self._features for handler in feature.callbacks()
        ]

    def inline_handler(self) -> InlineQueryHandler:
        return InlineQueryHandler(
            lambda ctx: self._renderer.answer_inline_query(
                [
                    handler(ctx)
                    for feature in self._features
                    for handler in feature.inlines()
                    if handler
                ],
                ctx,
            )
        )

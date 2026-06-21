import logging

from vasiniyo_chat_bot.config.dto import Config
from vasiniyo_chat_bot.telegram.feature_factory import FeatureFactory
from vasiniyo_chat_bot.telegram.handler.command_handler import CommandHandler
from vasiniyo_chat_bot.telegram.handler.inline_query_handler import InlineQueryHandler

logger = logging.getLogger(__name__)


class BotFeatureRegistry:
    def __init__(self, config: Config):
        factory = FeatureFactory(config)
        feature_factories = {
            "captcha": factory.captcha_feature,
            "help": factory.help_feature,
            "like": factory.like_feature,
            "drink": factory.drink_feature,
            "anime": factory.anime_feature,
            "titles": factory.titles_feature,
            "play": factory.play_feature,
            "reply": factory.reply_feature,
            "daily_size": factory.daily_size_feature,
        }
        self._features = [
            feature
            for feature in [
                factory() if mod in config.bot_settings.mods else None
                for mod, factory in feature_factories.items()
            ]
            if feature
        ]
        self._renderer = factory.renderer

    def my_commands(self) -> dict[str, str]:
        commands = {
            key: command
            for feature in self._features
            for key, command in feature.commands().items()
        }
        return {
            command.info.name: command.info.description for command in commands.values()
        }

    def message_handlers(self):
        return sorted(
            [handler for feature in self._features for handler in feature.messages()],
            key=lambda m: not isinstance(m, CommandHandler),
        )

    def callback_query_handlers(self):
        return [
            handler for feature in self._features for handler in feature.callbacks()
        ]

    def inline_handler(self):
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

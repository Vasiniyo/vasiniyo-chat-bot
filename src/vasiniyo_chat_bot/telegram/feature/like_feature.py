from injector import inject

from vasiniyo_chat_bot.config.dto import BotSettings
from vasiniyo_chat_bot.module.help.command import CommandInfo
from vasiniyo_chat_bot.module.help.command import CommandKey
from vasiniyo_chat_bot.module.like.like_controller import LikeController
from vasiniyo_chat_bot.telegram.bot_service import BotService
from vasiniyo_chat_bot.telegram.feature.feature import Feature


@inject
class LikeFeature(Feature):
    def __init__(
        self, settings: BotSettings, bot_service: BotService, controller: LikeController
    ):
        self._controller = controller
        super().__init__(
            settings, bot_service, all_commands=self._all_commands(settings.commands)
        )

    def _all_commands(self, commands: dict[CommandKey, CommandInfo]):
        return {
            CommandKey.LIKE: (commands.get(CommandKey.LIKE), self._controller.set_like),
            CommandKey.TOP_LIKES: (
                commands.get(CommandKey.TOP_LIKES),
                self._controller.top_likes,
            ),
        }

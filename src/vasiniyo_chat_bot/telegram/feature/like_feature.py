from vasiniyo_chat_bot.config.bot_settings_reader import CommandInfo
from vasiniyo_chat_bot.module.help.command_key import CommandKey
from vasiniyo_chat_bot.module.like.like_controller import LikeController
from vasiniyo_chat_bot.telegram.feature.feature import Feature


class LikeFeature(Feature):
    def __init__(
        self,
        bot_username: str,
        allowed_chats: list[str],
        controller: LikeController | None,
        commands: dict[CommandKey, CommandInfo],
    ):
        self._controller = controller
        super().__init__(
            bot_username, allowed_chats, all_commands=self._all_commands(commands)
        )

    def _all_commands(self, commands: dict[CommandKey, CommandInfo]):
        return {
            CommandKey.LIKE: (commands.get(CommandKey.LIKE), self._controller.set_like),
            CommandKey.TOP_LIKES: (
                commands.get(CommandKey.TOP_LIKES),
                self._controller.top_likes,
            ),
        }

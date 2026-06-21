from vasiniyo_chat_bot.config.bot_settings_reader import CommandInfo
from vasiniyo_chat_bot.module.help.command_key import CommandKey
from vasiniyo_chat_bot.module.play.play_controller import PlayController
from vasiniyo_chat_bot.telegram.feature.feature import Feature


class PlayFeature(Feature):
    def __init__(
        self,
        bot_username: str,
        allowed_chats: list[str],
        controller: PlayController | None,
        commands: dict[CommandKey, CommandInfo],
    ):
        self._controller = controller
        super().__init__(
            bot_username, allowed_chats, all_commands=self._all_commands(commands)
        )

    def _all_commands(self, commands: dict[CommandKey, CommandInfo]):
        return {
            CommandKey.PLAY: (
                commands.get(CommandKey.PLAY),
                self._controller.handle_play,
            ),
            CommandKey.PLAYERS: (
                commands.get(CommandKey.PLAYERS),
                self._controller.handle_players,
            ),
            CommandKey.WINNER: (
                commands.get(CommandKey.WINNER),
                self._controller.handle_winner,
            ),
            CommandKey.TOP_WINNERS: (
                commands.get(CommandKey.TOP_WINNERS),
                self._controller.handle_top_winners,
            ),
            CommandKey.TEST_NEW_CATEGORY: (
                commands.get(CommandKey.TEST_NEW_CATEGORY),
                self._controller.handle_test_new_category,
            ),
            CommandKey.TEST_NEW_WINNER: (
                commands.get(CommandKey.TEST_NEW_WINNER),
                self._controller.handle_test_new_winner,
            ),
        }

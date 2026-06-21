from vasiniyo_chat_bot.config.bot_settings_reader import CommandInfo
from vasiniyo_chat_bot.module.help.command_key import CommandKey
from vasiniyo_chat_bot.module.titles.titles_controller import TitlesController
from vasiniyo_chat_bot.module.titles.titles_payload_factory import TitlesPayloadFactory
from vasiniyo_chat_bot.telegram.feature.feature import Feature
from vasiniyo_chat_bot.telegram.filter import Filter
from vasiniyo_chat_bot.telegram.handler.query_handler import QueryHandler
from vasiniyo_chat_bot.telegram.handler.titles_query_handler import TitlesQueryHandler


class TitlesFeature(Feature):
    def __init__(
        self,
        bot_username: str,
        allowed_chats: list[str],
        controller: TitlesController | None,
        commands: dict[CommandKey, CommandInfo],
    ):
        self._controller = controller
        super().__init__(
            bot_username,
            allowed_chats,
            all_commands=self._all_commands(commands),
            callback_handlers=self._callback_handlers(allowed_chats),
        )

    def _all_commands(self, commands: dict[CommandKey, CommandInfo]):
        return {
            CommandKey.RENAME: (
                commands.get(CommandKey.RENAME),
                self._controller.handle_rename,
            )
        }

    def _callback_handlers(self, allowed_chats: list[str]) -> list[QueryHandler]:
        return [
            TitlesQueryHandler(
                allowed_chats,
                self._controller.dispatch_titles_callback,
                Filter(lambda call: TitlesPayloadFactory.has_titles_payload(call.data)),
            )
        ]

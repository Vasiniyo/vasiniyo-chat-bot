from vasiniyo_chat_bot.config.bot_settings_reader import CommandInfo
from vasiniyo_chat_bot.module.anime.anime_controller import AnimeController
from vasiniyo_chat_bot.module.anime.anime_payload_factory import AnimePayloadFactory
from vasiniyo_chat_bot.module.help.command_key import CommandKey
from vasiniyo_chat_bot.telegram.feature.feature import Feature
from vasiniyo_chat_bot.telegram.filter import Filter
from vasiniyo_chat_bot.telegram.handler.anime_query_handler import AnimeQueryHandler
from vasiniyo_chat_bot.telegram.handler.query_handler import QueryHandler


class AnimeFeature(Feature):
    def __init__(
        self,
        bot_username: str,
        allowed_chats: list[str],
        controller: AnimeController | None,
        commands: dict[CommandKey, CommandInfo],
    ):
        self._controller = controller
        commands: dict[CommandKey, CommandInfo]
        super().__init__(
            bot_username,
            allowed_chats,
            callback_handlers=self._callback_handlers(allowed_chats),
            inline_handler=[
                lambda _: (
                    commands.get(CommandKey.ANIME).name,
                    self._controller.handle_anime_command,
                )
            ],
        )

    def _callback_handlers(self, allowed_chats: list[str]) -> list[QueryHandler]:
        return [
            AnimeQueryHandler(
                allowed_chats,
                self._controller.dispatch_anime_callback,
                Filter(lambda call: AnimePayloadFactory.has_anime_payload(call.data)),
            )
        ]

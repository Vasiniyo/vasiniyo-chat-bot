from injector import inject

from vasiniyo_chat_bot.config.dto import BotSettings
from vasiniyo_chat_bot.module.anime.anime_controller import AnimeController
from vasiniyo_chat_bot.module.dto import Action
from vasiniyo_chat_bot.module.help.command import CommandKey
from vasiniyo_chat_bot.module.payload_factory import PayloadFactory
from vasiniyo_chat_bot.telegram.bot_service import BotService
from vasiniyo_chat_bot.telegram.feature.feature import Feature
from vasiniyo_chat_bot.telegram.filter import Filter
from vasiniyo_chat_bot.telegram.handler.query_handler import QueryHandler


@inject
class AnimeFeature(Feature):
    _valid_payload_actions = {Action.ANIME}

    def __init__(
        self,
        settings: BotSettings,
        bot_service: BotService,
        controller: AnimeController,
    ):
        self._controller = controller
        super().__init__(
            settings,
            bot_service,
            callback_handlers=self._callback_handlers(settings.allowed_chats),
            inline_handler=[
                lambda _: (
                    settings.commands[CommandKey.ANIME].name,
                    self._controller.handle_anime_command,
                )
            ],
        )

    def _callback_handlers(self, allowed_chats: list[str]) -> list[QueryHandler]:
        return [
            QueryHandler(
                allowed_chats,
                self._controller.dispatch_anime_callback,
                Filter(
                    lambda call: PayloadFactory.has_action(
                        call.data, self._valid_payload_actions
                    )
                ),
            )
        ]

from typing import Callable

from injector import inject

from vasiniyo_chat_bot.config.dto import BotSettings
from vasiniyo_chat_bot.module.dto import CallbackContext
from vasiniyo_chat_bot.module.dto import InlineQueryContext
from vasiniyo_chat_bot.module.dto import MessageContext
from vasiniyo_chat_bot.module.dto import Response
from vasiniyo_chat_bot.module.help.command import CommandInfo
from vasiniyo_chat_bot.module.help.command import CommandKey
from vasiniyo_chat_bot.telegram.bot_service import BotService
from vasiniyo_chat_bot.telegram.handler.command import Command
from vasiniyo_chat_bot.telegram.handler.command_handler import CommandHandler
from vasiniyo_chat_bot.telegram.handler.message_handler import MessageHandler
from vasiniyo_chat_bot.telegram.handler.query_handler import QueryHandler


@inject
class Feature:
    def __init__(
        self,
        settings: BotSettings,
        bot_service: BotService,
        *,
        message_handlers: list[MessageHandler] | None = None,
        callback_handlers: list[QueryHandler] | None = None,
        inline_handler: (
            list[Callable[[InlineQueryContext], tuple[str, Callable[[], Response]]]]
            | None
        ) = None,
        all_commands: (
            dict[
                CommandKey,
                tuple[
                    CommandInfo | None,
                    Callable[[MessageContext], None]
                    | Callable[[CallbackContext], None],
                ],
            ]
            | None
        ) = None,
    ):
        self._bot_username = bot_service.get_me().username
        self._allowed_chats = settings.allowed_chats
        self._message_handlers = message_handlers or []
        self._callback_handlers = callback_handlers or []
        self._inline_handlers = inline_handler or []
        self._all_commands = all_commands or {}

    def commands(self) -> dict[CommandKey, Command]:
        return {
            key: Command(info, handler)
            for key, (info, handler), in self._all_commands.items()
            if info is not None
        }

    def messages(self) -> list[MessageHandler]:
        return [*self._known_commands(), *self._message_handlers]

    def callbacks(self) -> list[QueryHandler]:
        return self._callback_handlers

    def inlines(
        self,
    ) -> list[Callable[[InlineQueryContext], tuple[str, Callable[[], Response]]]]:
        return self._inline_handlers

    def _known_commands(self) -> list[MessageHandler]:
        return [
            CommandHandler(self._bot_username, self._allowed_chats, command)
            for command in self.commands().values()
        ]

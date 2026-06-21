from typing import Callable

from vasiniyo_chat_bot.config.bot_settings_reader import CommandInfo
from vasiniyo_chat_bot.module.dto import InlineCallbackContext
from vasiniyo_chat_bot.module.dto import MessageContext
from vasiniyo_chat_bot.module.dto import Response
from vasiniyo_chat_bot.module.help.command_key import CommandKey
from vasiniyo_chat_bot.telegram.feature.command import Command
from vasiniyo_chat_bot.telegram.handler.command_handler import CommandHandler
from vasiniyo_chat_bot.telegram.handler.message_handler import MessageHandler
from vasiniyo_chat_bot.telegram.handler.query_handler import QueryHandler


class Feature:
    def __init__(
        self,
        bot_username: str,
        allowed_chats: list[str],
        *,
        message_handlers: list[MessageHandler] = None,
        callback_handlers: list[QueryHandler] = None,
        inline_handler: list[
            Callable[[InlineCallbackContext], tuple[str, Callable[[], Response]]]
        ] = None,
        all_commands: dict[
            CommandKey, tuple[CommandInfo, Callable[[MessageContext], None]]
        ] = None,
    ):
        self._bot_username = bot_username
        self._allowed_chats = allowed_chats
        self._message_handlers = message_handlers or []
        self._callback_handlers = callback_handlers or []
        self._inline_handlers = inline_handler or []
        self._all_commands = all_commands or {}

    def commands(self) -> dict[CommandKey, Command]:
        return {
            key: Command(module, handler)
            for key, (module, handler), in self._all_commands.items()
            if module
        }

    def messages(self) -> list[MessageHandler]:
        return [*self._known_commands(), *self._message_handlers]

    def callbacks(self) -> list[QueryHandler]:
        return self._callback_handlers

    def inlines(
        self,
    ) -> list[Callable[[InlineCallbackContext], tuple[str, Callable[[], Response]]]]:
        return self._inline_handlers

    def _known_commands(self) -> list[MessageHandler]:
        return [
            CommandHandler(self._bot_username, self._allowed_chats, command)
            for command in self.commands().values()
        ]

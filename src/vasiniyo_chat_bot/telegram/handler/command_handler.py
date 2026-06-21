import logging

from telebot.types import Message

from vasiniyo_chat_bot.module.dto import MessageContext
from vasiniyo_chat_bot.telegram.feature.command import Command
from vasiniyo_chat_bot.telegram.filter import Filter
from vasiniyo_chat_bot.telegram.handler.message_handler import MessageHandler

logger = logging.getLogger(__name__)


class CommandHandler(MessageHandler):
    def __init__(
        self, bot_username: str, allowed_chats: list[str], command: Command
    ) -> None:
        self.bot_username = bot_username
        self._command = command
        super().__init__(
            allowed_chats, self._get_handler(command), Filter(self._command_for_bot)
        )

    def _get_handler(self, command: Command):
        def inner(ctx: MessageContext):
            logger.info(
                "handle_command",
                extra={
                    "command": self._command.info.name,
                    "chat_id": ctx.chat_id,
                    "user_id": ctx.user_id,
                },
            )
            command.handler(ctx)

        return inner

    def _command_for_bot(self, message: Message) -> bool:
        if not message.text:
            return False
        c = message.text.lstrip().split()
        if not c:
            return False
        x = c[0].split("@")
        if len(x) == 1:
            return x[0] == self._command.info.name
        return x[0] == self._command.info.name and x[1] == self.bot_username

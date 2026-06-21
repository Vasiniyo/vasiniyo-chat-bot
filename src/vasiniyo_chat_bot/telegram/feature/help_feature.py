from telebot.types import Message

from vasiniyo_chat_bot.config.bot_settings_reader import CommandInfo
from vasiniyo_chat_bot.module.dto import UserContext
from vasiniyo_chat_bot.module.help.command_key import CommandKey
from vasiniyo_chat_bot.module.help.help_controller import HelpController
from vasiniyo_chat_bot.telegram.feature.feature import Feature
from vasiniyo_chat_bot.telegram.filter import Filter
from vasiniyo_chat_bot.telegram.handler.message_handler import MessageHandler


class HelpFeature(Feature):
    def __init__(
        self,
        bot_username: str,
        allowed_chats: list[str],
        controller: HelpController | None,
        commands: dict[CommandKey, CommandInfo],
    ):
        all_commands = self._get_all_commands(controller, commands)
        command_names = {module.name for module, _ in all_commands.values()}
        message_handlers = self._message_handlers(
            allowed_chats, controller, bot_username, command_names
        )
        super().__init__(
            bot_username,
            allowed_chats,
            message_handlers=message_handlers,
            all_commands=all_commands,
        )

    @staticmethod
    def _get_all_commands(
        controller: HelpController, commands: dict[CommandKey, CommandInfo]
    ):
        def _help_handler(ctx: UserContext):
            return controller.show_help(ctx, list(commands.values()))

        return {CommandKey.HELP: (commands.get(CommandKey.HELP), _help_handler)}

    def _message_handlers(
        self, allowed_chats, controller, bot_username: str, command_names: set[str]
    ):
        return [
            MessageHandler(
                allowed_chats,
                lambda ctx: controller.handle_unknown_command(
                    ctx, self._all_commands.get(CommandKey.HELP, None)[0]
                ),
                Filter(HelpFeature._unknown_command(command_names, bot_username)),
            )
        ]

    @staticmethod
    def _unknown_command(command_names: set[str], bot_username: str):
        def inner(message: Message) -> bool:
            text = message.text
            if not text:
                return False
            command, _, username = text.lstrip().split(maxsplit=1)[0].partition("@")
            return username == bot_username and command not in command_names

        return inner

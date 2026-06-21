from vasiniyo_chat_bot.config.bot_settings_reader import CommandInfo
from vasiniyo_chat_bot.module.dto import UserContext
from vasiniyo_chat_bot.module.help.help_response_factory import HelpResponseFactory
from vasiniyo_chat_bot.module.renderer import Renderer


class HelpController:
    def __init__(
        self, response_factory: HelpResponseFactory, renderer: Renderer
    ) -> None:
        self._response_factory = response_factory
        self._renderer = renderer

    def show_help(self, ctx: UserContext, commands: list[CommandInfo]):
        response = self._response_factory.send(commands)
        self._renderer.send(response, ctx)

    def handle_unknown_command(self, ctx: UserContext, help_command: CommandInfo):
        response = self._response_factory.send_unknown_command(help_command)
        self._renderer.send(response, ctx)

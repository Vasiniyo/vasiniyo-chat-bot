from injector import inject

from vasiniyo_chat_bot.module.dto import MessageContext
from vasiniyo_chat_bot.module.help.command import CommandInfo
from vasiniyo_chat_bot.module.help.help_response_factory import HelpResponseFactory
from vasiniyo_chat_bot.module.renderer import Renderer


@inject
class HelpController:
    def __init__(
        self, response_factory: HelpResponseFactory, renderer: Renderer
    ) -> None:
        self._response_factory = response_factory
        self._renderer = renderer

    def show_help(self, ctx: MessageContext, commands: list[CommandInfo]):
        response = self._response_factory.send(commands)
        self._renderer.send(response, ctx)

    def handle_unknown_command(self, ctx: MessageContext, help_command: CommandInfo):
        response = self._response_factory.send_unknown_command(help_command)
        self._renderer.send(response, ctx)

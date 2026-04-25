from vasiniyo_chat_bot.module.help.command_key import CommandKey
from vasiniyo_chat_bot.telegram.dto import UserContext
from vasiniyo_chat_bot.telegram.renderer.help_response_factory import (
    HelpResponseFactory,
)
from vasiniyo_chat_bot.telegram.renderer.renderer import Renderer


class HelpController:
    def __init__(
        self, response_factory: HelpResponseFactory, renderer: Renderer
    ) -> None:
        self._response_factory = response_factory
        self._renderer = renderer

    def show_help(self, ctx: UserContext, commands: dict[CommandKey, str]):
        response = self._response_factory.send(commands)
        self._renderer.send(response, ctx)

    def handle_unknown_command(self, ctx: UserContext):
        response = self._response_factory.send_unknown_command()
        self._renderer.send(response, ctx)

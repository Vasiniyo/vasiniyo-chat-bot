from telebot.types import Message

from vasiniyo_chat_bot.module.help.command_key import CommandKey
from vasiniyo_chat_bot.telegram.renderer.help_renderer import HelpRenderer


class HelpController:
    def __init__(self, help_renderer: HelpRenderer) -> None:
        self.help_renderer = help_renderer

    def show_help(self, message: Message, commands: dict[CommandKey, str]):
        self.help_renderer.send(commands, message.chat.id, message.id)

    def handle_unknown_command(self, message: Message):
        self.help_renderer.send_unknown_command(message.chat.id, message.id)

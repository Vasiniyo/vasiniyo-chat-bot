from vasiniyo_chat_bot.config.bot_settings_reader import CommandInfo
from vasiniyo_chat_bot.module.dto import BoldTemplate
from vasiniyo_chat_bot.module.dto import ItalicTemplate
from vasiniyo_chat_bot.module.dto import Response


class HelpResponseFactory:
    @staticmethod
    def send(all_commands: list[CommandInfo]):
        text_commands = [
            f"{command.name} - {command.description}\n"
            for command in all_commands
            if not command.is_inline
        ]
        text_inlines = [
            item
            for command in all_commands
            if command.is_inline
            for item in [ItalicTemplate(command.name), f" - {command.description}\n"]
        ]
        text = [
            text_commands and BoldTemplate(f"Доступные команды:\n"),
            *text_commands,
            text_inlines and BoldTemplate("\nInline-команды:\n"),
            *text_inlines,
        ]
        return Response(text_units=text)

    @staticmethod
    def send_unknown_command(help_command: CommandInfo | None = None):
        text = (
            f"🤯 Я такой команды не знаю! "
            f"Посмотреть доступные можно при помощи {help_command.name}"
            if help_command
            else ""
        )
        return Response(text_units=text)

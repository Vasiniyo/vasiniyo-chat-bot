import os
import sys

from injector import inject

from vasiniyo_chat_bot.config.dto import BotSettings
from vasiniyo_chat_bot.config.dto import Config
from vasiniyo_chat_bot.module.help.command import CommandInfo
from vasiniyo_chat_bot.module.help.command import CommandKey


@inject
class BotSettingsReader:
    _valid_mods = [
        # fmt: off
        "like", "drink", "daily_size",
        "anime", "titles", "play",
        "reply", "captcha", "help"
        # fmt: on
    ]
    _command_mods = {
        # fmt: off
        "like": [CommandKey.TOP_LIKES, CommandKey.LIKE],
        "titles": [CommandKey.RENAME],
        "play": [CommandKey.PLAY, CommandKey.PLAYERS, CommandKey.WINNER, CommandKey.TOP_WINNERS],
        "help": [CommandKey.HELP],
        "test": [CommandKey.TEST_NEW_CATEGORY, CommandKey.TEST_NEW_WINNER],
        # fmt: on
    }
    _inner_mods = {
        "anime": [CommandKey.ANIME],
        "drink": [CommandKey.DRINK_OR_NOT],
        "daily_size": [CommandKey.DAILY_SIZE],
    }

    def __init__(self, config: Config) -> None:
        self._config = config

    def load(self) -> BotSettings:
        api_token = os.environ.get("BOT_API_TOKEN")
        if api_token is None:
            raise Exception("BOT_API_TOKEN token not set")
        allowed_chats = os.environ.get("ACCESS_ID_GROUP", "*").split(";")
        if len(allowed_chats) == 1 and allowed_chats[0] == "":
            allowed_chats = ["*"]
        mods_section = self._config.section.get("mods", self._valid_mods)
        if "--test" in sys.argv or os.environ.get("TEST_MODE", "").lower() == "true":
            mods_section.append("test")
        command_mods = self._extract(
            self._filter_mods(self._command_mods, mods_section),
            self._config.section.get("commands", {}),
            is_inline=False,
        )
        inner_mods = self._extract(
            self._filter_mods(self._inner_mods, mods_section),
            self._config.section.get("inlines", {}),
            is_inline=True,
        )
        return BotSettings(
            api_token=api_token,
            allowed_chats=allowed_chats,
            language=self._config.section.get("lang", "ru"),
            mods=mods_section,
            commands=command_mods | inner_mods,
        )

    @staticmethod
    def _filter_mods(
        cmds: dict[str, list[CommandKey]], mods_section
    ) -> dict[str, list[CommandKey]]:
        return {
            mod: command_keys
            for mod, command_keys in cmds.items()
            if mod in mods_section
        }

    @staticmethod
    def _extract(cmds: dict[str, list[CommandKey]], section, *, is_inline: bool):
        cmd_section = lambda k: section.get(k.name.lower(), {})
        return {
            key: CommandInfo(
                cmd_section(key).get("name", f"/{key.name.lower()}"),
                cmd_section(key).get("desc", "Описание отсутствует."),
                is_inline=is_inline,
            )
            for key in CommandKey
            if key in [key for keys in cmds.values() for key in keys]
        }

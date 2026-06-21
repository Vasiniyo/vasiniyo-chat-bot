from dataclasses import dataclass
import logging
import os
import sys

from telebot import TeleBot

from vasiniyo_chat_bot.module.help.command_key import CommandKey

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CommandInfo:
    name: str
    description: str
    is_inline: bool


@dataclass(frozen=True)
class BotSettings:
    bot: TeleBot | None
    allowed_chats: list[str]
    language: str
    mods: list[str]
    commands: dict[CommandKey, CommandInfo]


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

    def __init__(self, section: dict[str, any]) -> None:
        self._section = section

    def load(self) -> BotSettings:
        api_token = os.environ.get("BOT_API_TOKEN")
        try:
            bot = TeleBot(api_token)
        except Exception as e:
            logger.error("BOT_API_TOKEN is not set or invalid")
            raise e
        allowed_chats = os.environ.get("ACCESS_ID_GROUP", "*").split(";")
        if len(allowed_chats) == 1 and allowed_chats[0] == "":
            allowed_chats = ["*"]
        mods_section = self._section.get("mods", self._valid_mods)
        if "--test" in sys.argv or os.environ.get("TEST_MODE", "").lower() == "true":
            mods_section.append("test")
        command_mods = self._extract(
            self._filter_mods(self._command_mods, mods_section),
            self._section.get("commands", {}),
            is_inline=False,
        )
        inner_mods = self._extract(
            self._filter_mods(self._inner_mods, mods_section),
            self._section.get("inlines", {}),
            is_inline=True,
        )
        return BotSettings(
            bot=bot,
            allowed_chats=allowed_chats,
            language=self._section.get("lang", "ru"),
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

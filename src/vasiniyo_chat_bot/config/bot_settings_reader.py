from dataclasses import dataclass
import logging
import os
import sys

from telebot import TeleBot

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BotSettings:
    bot: TeleBot | None
    allowed_chats: list[str]
    language: str
    mods: list[str]


class BotSettingsReader:
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
        mods = self._section.get(
            "mods", ["like", "drink", "anime", "titles", "play", "reply", "captcha"]
        )
        if "--test" in sys.argv or os.environ.get("TEST_MODE", "").lower() == "true":
            mods.append("test")
        return BotSettings(
            bot=bot,
            allowed_chats=allowed_chats,
            language=self._section.get("lang", "ru"),
            mods=mods,
        )

from dataclasses import dataclass
from typing import Any

from injector import inject

from vasiniyo_chat_bot.module.help.command import CommandInfo
from vasiniyo_chat_bot.module.help.command import CommandKey


@inject
@dataclass(frozen=True)
class Config:
    section: dict[str, Any]


@inject
@dataclass(frozen=True)
class BotSettings:
    api_token: str
    allowed_chats: list[str]
    language: str
    mods: list[str]
    commands: dict[CommandKey, CommandInfo]

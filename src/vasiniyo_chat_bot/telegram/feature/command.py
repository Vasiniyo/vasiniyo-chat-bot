from dataclasses import dataclass
from typing import Callable

from vasiniyo_chat_bot.config.bot_settings_reader import CommandInfo
from vasiniyo_chat_bot.module.dto import MessageContext


@dataclass(frozen=True)
class Command:
    info: CommandInfo
    handler: Callable[[MessageContext], None]

from dataclasses import dataclass
from typing import Callable

from vasiniyo_chat_bot.module.dto import CallbackContext
from vasiniyo_chat_bot.module.dto import MessageContext
from vasiniyo_chat_bot.module.help.command import CommandInfo


@dataclass(frozen=True)
class Command:
    info: CommandInfo
    handler: Callable[[MessageContext], None] | Callable[[CallbackContext], None]

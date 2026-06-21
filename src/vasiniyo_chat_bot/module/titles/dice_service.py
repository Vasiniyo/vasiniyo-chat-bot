from __future__ import annotations

from typing import Protocol

from vasiniyo_chat_bot.module.dto import UserContext


class DiceService(Protocol):
    def roll_match(self, expected_value: int, ctx: UserContext) -> bool: ...
    def roll_random(self, ctx: UserContext) -> bool: ...

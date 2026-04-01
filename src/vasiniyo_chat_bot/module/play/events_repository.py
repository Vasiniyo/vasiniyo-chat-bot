from __future__ import annotations

from typing import Protocol

from vasiniyo_chat_bot.module.likes.dto import Leaderboard


class EventsRepository(Protocol):
    def insert_winner(self, chat_id: int, user_id: int, event_id: int) -> int: ...
    def get_last_winner(self, chat_id: int, event_id: int) -> int | None: ...
    def is_day_passed(self, chat_id: int, event_id: int) -> bool: ...
    def get_leaderboard(
        self, chat_id: int, event_id: int, limit: int
    ) -> Leaderboard: ...

from __future__ import annotations

from typing import Protocol

from vasiniyo_chat_bot.module.likes.dto import Leaderboard


class LikesRepository(Protocol):
    def like_and_count(
        self, chat_id: int, from_user_id: int, to_user_id: int
    ) -> int: ...
    def get_leaderboard(self, chat_id: int, limit: int) -> Leaderboard: ...

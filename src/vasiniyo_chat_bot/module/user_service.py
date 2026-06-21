import datetime
from typing import Protocol

from vasiniyo_chat_bot.module.dto import UserContext


class UserService(Protocol):
    _cache = {}

    def get_username(
        self, chat_id: int, user_id: int, is_active: bool = None
    ) -> str | None: ...
    def get_title(self, ctx: UserContext) -> str | None: ...
    def set_title(self, ctx: UserContext, title: str) -> str | None: ...
    def set_default_title(self, ctx: UserContext) -> str | None: ...
    def get_photo(self, winner_id) -> bytes | None: ...
    def ban(self, ctx) -> None: ...

    def invalidate_cache(self, chat_id: int, user_id: int) -> None:
        today = datetime.date.today().toordinal()
        self._cache.pop((chat_id, user_id, True, today), None)
        self._cache.pop((chat_id, user_id, False, today), None)
        self._cache.pop((chat_id, user_id, None, today), None)

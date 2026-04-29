import datetime
from functools import lru_cache
from io import BytesIO
import logging
from typing import Protocol

from telebot.types import ChatMemberBanned, ChatMemberLeft, User

from vasiniyo_chat_bot.safely_bot_utils import daily_hash
from vasiniyo_chat_bot.telegram.bot_service import BotService
from vasiniyo_chat_bot.telegram.dto import UserContext


class UserService(Protocol):
    def get_username(
        self, chat_id: int, user_id: int, is_active: bool = None
    ) -> str | None: ...
    def get_title(self, ctx: UserContext) -> str | None: ...
    def set_title(self, ctx: UserContext, title: str) -> str | None: ...
    def set_default_title(self, ctx: UserContext) -> str | None: ...
    def get_photo(self, winner_id) -> bytes | None: ...
    def ban(self, ctx) -> None: ...


class TelegramUserService(UserService):
    _cache = {}

    def __init__(self, client: BotService):
        self._client = client

    def invalidate_cache(self, chat_id: int, user_id: int) -> None:
        today = datetime.date.today().toordinal()
        self._cache.pop((chat_id, user_id, True, today), None)
        self._cache.pop((chat_id, user_id, False, today), None)
        self._cache.pop((chat_id, user_id, None, today), None)

    def get_username(
        self, chat_id: int, user_id: int, is_active: bool = None
    ) -> str | None:
        key = (chat_id, user_id, is_active, datetime.date.today().toordinal())
        value = self._cache.get(key)
        if key in self._cache:
            return value
        if not is_active:
            user = self.get_user(chat_id, user_id)
            value = user and (user.username or user.full_name)
        else:
            member = self._client.get_chat_member(chat_id, user_id)
            if (
                member
                and not isinstance(member, ChatMemberLeft)
                and not isinstance(member, ChatMemberBanned)
            ):
                value = member.user and (member.user.username or member.user.full_name)
        self._cache[key] = value
        return value

    def get_title(self, ctx: UserContext) -> str | None:
        return self._client.get_admin_title(ctx)

    def set_title(self, ctx: UserContext, title: str) -> str | None:
        return self._client.set_title(ctx, title)

    def set_default_title(self, ctx: UserContext) -> str | None:
        return self._client.set_title(ctx, "украдено")

    def get_user(self, chat_id: int, user_id: int) -> User | None:
        member = self._client.get_chat_member(chat_id, user_id)
        return member.user if member else None

    def get_photo(self, user_id) -> BytesIO | None:
        return self._client.get_profile_photo(user_id)

    def ban(self, ctx: UserContext) -> None:
        self._client.ban_chat_member(ctx)

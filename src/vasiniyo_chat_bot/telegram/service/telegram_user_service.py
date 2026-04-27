from io import BytesIO
from typing import Protocol

from telebot.types import User

from vasiniyo_chat_bot.telegram.bot_service import BotService
from vasiniyo_chat_bot.telegram.dto import UserContext


class UserService(Protocol):
    def get_username(self, chat_id: int, user_id: int) -> str | None: ...
    def get_title(self, ctx: UserContext) -> str | None: ...
    def set_title(self, ctx: UserContext, title: str) -> str | None: ...
    def set_default_title(self, ctx: UserContext) -> str | None: ...
    def get_photo(self, winner_id) -> bytes | None: ...
    def ban(self, ctx) -> None: ...


class TelegramUserService(UserService):
    def __init__(self, client: BotService):
        self._client = client

    def get_username(self, chat_id: int, user_id: int) -> str | None:
        user = self.get_user(chat_id, user_id)
        return user and (user.username or user.full_name)

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

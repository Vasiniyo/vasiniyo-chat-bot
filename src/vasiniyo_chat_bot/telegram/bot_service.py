import asyncio
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
import logging
import random
import threading
from typing import Callable

from telebot import REPLY_MARKUP_TYPES, TeleBot
from telebot.types import (
    ChatMember,
    File,
    InputFile,
    InputMediaPhoto,
    LinkPreviewOptions,
    Message,
    ReplyParameters,
    User,
)

from vasiniyo_chat_bot.module.likes.dto import Leaderboard
from vasiniyo_chat_bot.safely_bot_utils import safe_wrapper

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UserTemplate:
    chat_id: int
    user_id: int


@dataclass(frozen=True)
class BoldTemplate:
    text: str


@dataclass(frozen=True)
class ItalicTemplate:
    text: str


class BotService:
    _dices = {
        "⚽": {"weight": 25, "win_values": (3, 4, 5)},
        "🏀": {"weight": 25, "win_values": (4, 5)},
        "🎯": {"weight": 54, "win_values": (6,)},
        "🎳": {"weight": 54, "win_values": (6,)},
        "🎰": {"weight": 112, "win_values": (1, 22, 43, 64)},
    }
    _loop = asyncio.new_event_loop()

    def __init__(self, bot: TeleBot):
        self.bot = bot
        self._dice_keys = list(self._dices.keys())
        self._dice_weights = [self._dices[item]["weight"] for item in self._dice_keys]
        threading.Thread(target=self._start_loop, daemon=True).start()

    @lru_cache
    def get_me(self):
        logger.info("bot_get_me")
        return self.bot.get_me()

    def get_user(self, chat_id: int, user_id: int) -> User | None:
        logger.info("get_chat_member", extra={"chat_id": chat_id, "user_id": user_id})
        try:
            return self.bot.get_chat_member(chat_id, user_id).user
        except:
            logger.info(
                "member_not_found", extra={"chat_id": chat_id, "user_id": user_id}
            )
            return None

    @safe_wrapper(default="Забытый пользователь")
    def get_username(self, chat_id: int, user_id: int) -> str:
        user = self.get_user(chat_id, user_id)
        if user is None:
            return "Забытый пользователь"
        if user.username is None:
            return user.full_name
        return user.username

    @safe_wrapper(default=None)
    def get_profile_photo(self, user_id: int) -> bytes | None:
        file_info = self.get_user_profile_photo_file_info(user_id)
        if not file_info:
            return None
        logger.info("download_file", extra={"file_path": file_info.file_path})
        return self.bot.download_file(file_info.file_path)

    @safe_wrapper(default=None)
    def get_admin_title(self, chat_id: int, user_id: int) -> str | None:
        for admin in self.get_chat_administrators(chat_id):
            if admin.user.id == user_id:
                return admin.custom_title
        return None

    @safe_wrapper(default=[])
    def get_chat_administrators(self, chat_id: int) -> list[ChatMember]:
        logger.info("fetch_admins", extra={"chat_id": chat_id})
        return self.bot.get_chat_administrators(chat_id)

    @safe_wrapper(default=None)
    def get_user_profile_photo_file_info(self, user_id: int) -> File | None:
        logger.info("get_user_profile_photo", extra={"user_id": user_id})
        photo = self.bot.get_user_profile_photos(user_id, limit=1)
        file_id = photo.photos[0][-1].file_id
        logger.info("get_file", extra={"file_id": file_id})
        return self.bot.get_file(file_id) if photo.photos else None

    def set_default_title(self, chat_id: int, user_id: int):
        return self.set_title(chat_id, user_id, "украдено")

    @safe_wrapper(default=None)
    def set_title(self, chat_id: int, user_id: int, title: str) -> str | None:
        if len(title) > 16:
            return None
        admins = {
            admin.user.id: admin for admin in self.get_chat_administrators(chat_id)
        }
        user = admins.get(user_id)
        bot_user = admins.get(self.get_me().id)
        if bot_user is None:
            return None
        if (not user) and bot_user.can_promote_members and bot_user.can_invite_users:
            logger.info(
                "promote_user",
                extra={
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "permissions": ["can_invite_users"],
                },
            )
            self.bot.promote_chat_member(chat_id, user_id, can_invite_users=True)
        if not user or not user.can_be_edited:
            return None
        logger.info(
            "set_title", extra={"chat_id": chat_id, "user_id": user_id, "title": title}
        )
        self.bot.set_chat_administrator_custom_title(chat_id, user_id, title)
        return title

    @safe_wrapper(default=None)
    def edit_message_text_later(
        self,
        text_units: str | list[str | UserTemplate | BoldTemplate | ItalicTemplate],
        chat_id: int,
        message_id: int,
        delay: int = 5,
        should_edit: Callable[[], bool] = lambda: True,
    ) -> None:
        async def edit_message():
            await asyncio.sleep(delay)
            if should_edit():
                self.edit_message_text(text_units, chat_id, message_id)

        logger.info(
            "schedule editing",
            extra={"chat_id": chat_id, "message_id": message_id, "delay": delay},
        )
        asyncio.run_coroutine_threadsafe(edit_message(), self._loop)

    @safe_wrapper(default=None)
    def edit_message_text(
        self,
        text_units: str | list[str | UserTemplate | BoldTemplate | ItalicTemplate],
        chat_id: int,
        message_id: int,
        reply_markup: REPLY_MARKUP_TYPES | None = None,
        is_disabled_preview: bool = True,
    ) -> None:
        text = self._to_text(text_units)
        logger.info(
            "edit_message_text",
            extra={"chat_id": chat_id, "message_id": message_id, "message_text": text},
        )
        self.bot.edit_message_text(
            text,
            chat_id,
            message_id,
            parse_mode="MarkdownV2",
            link_preview_options=LinkPreviewOptions(is_disabled=is_disabled_preview),
            reply_markup=reply_markup,
        )

    @safe_wrapper(default=None)
    def edit_message_caption(
        self,
        chat_id: int,
        message_id: int,
        caption: str,
        reply_markup: REPLY_MARKUP_TYPES | None = None,
    ):
        logger.info(
            "edit_message_caption",
            extra={"chat_id": chat_id, "message_id": message_id, "caption": caption},
        )
        self.bot.edit_message_caption(
            chat_id=chat_id,
            message_id=message_id,
            caption=caption,
            reply_markup=reply_markup,
        )

    @safe_wrapper(default=None)
    def edit_message_media(
        self,
        photo: BytesIO,
        chat_id: int,
        message_id: int,
        caption: str | None = None,
        reply_markup: REPLY_MARKUP_TYPES | None = None,
    ):
        logger.info(
            "edit_message_media", extra={"chat_id": chat_id, "message_id": message_id}
        )
        self.bot.edit_message_media(
            media=InputMediaPhoto(InputFile(photo), caption, "HTML"),
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup,
        )

    @safe_wrapper(default=None)
    def clear_markup(self, chat_id: int, message_id: int):
        logger.info(
            "clear_message_markup", extra={"chat_id": chat_id, "message_id": message_id}
        )
        self.bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)

    def roll_dice(self, expected_value: int, chat_id: int, message_id: int) -> bool:
        logger.info(
            "send_dice",
            extra={"chat_id": chat_id, "message_id": message_id, "emoji": "🎲"},
        )
        dice_message = self.bot.send_dice(
            chat_id, reply_to_message_id=message_id, emoji="🎲"
        )
        return dice_message.dice.value == expected_value

    def roll_random_dice(self, chat_id: int, message_id: int) -> bool:
        reply_parameters = (
            ReplyParameters(message_id=message_id, allow_sending_without_reply=True)
            if message_id
            else None
        )
        emoji = random.choices(self._dice_keys, weights=self._dice_weights)[0]
        logger.info(
            "send_dice",
            extra={"chat_id": chat_id, "message_id": message_id, "emoji": emoji},
        )
        dice_message = self.bot.send_dice(
            chat_id, emoji=emoji, reply_parameters=reply_parameters
        )
        win_values = self._dices[dice_message.dice.emoji]["win_values"]
        return dice_message.dice.value in win_values

    @safe_wrapper(default=None)
    def answer_callback_query(self, text: str, query_id: int) -> None:
        logger.info(
            "answer_callback_query", extra={"query_id": query_id, "query": text}
        )
        self.bot.answer_callback_query(query_id, text=text, cache_time=3)

    @safe_wrapper(default=None)
    def send_message(
        self,
        text_units: str | list[str | UserTemplate | BoldTemplate | ItalicTemplate],
        chat_id: int,
        message_id: int | None = None,
        reply_markup: REPLY_MARKUP_TYPES | None = None,
        is_disabled_preview: bool = True,
    ) -> None:
        reply_parameters = (
            ReplyParameters(message_id=message_id, allow_sending_without_reply=True)
            if message_id
            else None
        )
        text = self._to_text(text_units)
        logger.info(
            "send_message",
            extra={"chat_id": chat_id, "message_id": message_id, "message_text": text},
        )
        self.bot.send_message(
            chat_id,
            text,
            parse_mode="MarkdownV2",
            disable_notification=True,
            link_preview_options=LinkPreviewOptions(is_disabled=is_disabled_preview),
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
        )

    @safe_wrapper(default=None)
    def send_sticker(
        self, file_id: str, chat_id: int, message_id: int | None = None
    ) -> None:
        logger.info(
            "send_sticker",
            extra={"chat_id": chat_id, "message_id": message_id, "file_id": file_id},
        )
        self.bot.send_sticker(
            chat_id,
            file_id,
            reply_parameters=ReplyParameters(
                message_id=message_id, allow_sending_without_reply=True
            ),
        )

    @safe_wrapper(default=None)
    def send_photo(
        self,
        photo: BytesIO,
        chat_id: int,
        message_id: int | None = None,
        caption: (
            str | list[str | UserTemplate | BoldTemplate | ItalicTemplate] | None
        ) = None,
        reply_markup: REPLY_MARKUP_TYPES | None = None,
    ) -> Message:
        logger.info("send_photo", extra={"chat_id": chat_id, "message_id": message_id})
        reply_parameters = (
            ReplyParameters(message_id=message_id, allow_sending_without_reply=True)
            if message_id
            else None
        )
        return self.bot.send_photo(
            chat_id,
            photo=InputFile(photo),
            caption=self._to_text(caption) if caption else None,
            parse_mode="MarkdownV2",
            disable_notification=True,
            reply_markup=reply_markup,
            reply_parameters=reply_parameters,
        )

    @safe_wrapper(default=None)
    def send_leaderboard(
        self,
        leaderboard: Leaderboard,
        header: str,
        chat_id: int,
        message_id: int | None = None,
        ignore_value: bool = False,
    ) -> None:
        units = [header + "\n"] + [
            item
            for position, row in enumerate(leaderboard.rows)
            for item in [
                f"{position + 1}. ",
                UserTemplate(leaderboard.chat_id, row.user_id),
                "\n" if ignore_value else f" — {row.value}\n",
            ]
        ]
        self.send_message(units, chat_id, message_id)

    @safe_wrapper(default=None)
    def delete_message(self, chat_id: int, message_id: int) -> None:
        logger.info(
            f"delete_message", extra={"chat_id": chat_id, "message_id": message_id}
        )
        self.bot.delete_message(chat_id, message_id)

    @safe_wrapper(default=None)
    def ban_chat_member(self, chat_id, user_id) -> None:
        logger.info(f"ban_user", extra={"chat_id": chat_id, "user_id": user_id})
        self.bot.ban_chat_member(chat_id, user_id)

    def _start_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _to_text(
        self, text_units: str | list[str | UserTemplate | BoldTemplate | ItalicTemplate]
    ) -> str:
        if isinstance(text_units, str):
            return self._escape_markdown_v2(text_units)
        text = ""
        for unit in text_units:
            if isinstance(unit, UserTemplate):
                user = self.get_user(unit.chat_id, unit.user_id)
                text += self._to_link_user_v2(user)
            elif isinstance(unit, BoldTemplate):
                text += f"*{self._escape_markdown_v2(unit.text)}*"
            elif isinstance(unit, ItalicTemplate):
                text += f"_{self._escape_markdown_v2(unit.text)}_"
            else:
                text += self._escape_markdown_v2(unit)
        return text

    def _to_link_user_v2(self, user: User) -> str:
        """MarkdownV2 compatible user link"""
        if user is None:
            return "Забытый пользователь"
        first_name_escaped = self._escape_markdown_v2(user.first_name)
        if user.username:
            username_escaped = self._escape_markdown_v2(user.username)
            url = f"https://t\\.me/{username_escaped}"
            return f"{first_name_escaped} \\([{username_escaped}]({url})\\)"

        return first_name_escaped

    @staticmethod
    def _escape_markdown_v2(text: str) -> str:
        if text is None:
            return ""
        special_chars = "_*[]()~`>#+-=|{}.!"
        for char in special_chars:
            text = text.replace(char, f"\\{char}")
        return text

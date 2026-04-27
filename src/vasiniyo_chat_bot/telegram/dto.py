from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from io import BytesIO

from telebot.types import InlineKeyboardMarkup


class Action(Enum):
    ROLL_RANDOM_D6 = "0"
    ROLL_D6 = "1"
    OPEN_RENAME_MENU = "2"
    OPEN_STEAL_MENU = "3"
    STEAL_TITLE = "4"
    OPEN_TITLES_BAG = "5"
    SET_TITLE_BAG = "6"
    CAPTCHA_UPDATE = "7"
    ANIME = "8"


class Field(Enum):
    ACTION_TYPE = "0"
    USER_ID = "1"
    DICE_VALUE = "2"
    PAGE = "3"
    TARGET_USER_ID = "4"
    TITLE_BAG_ID = "5"
    ANIME_GENRE = "6"


@dataclass(frozen=True)
class Pageable:
    page: int
    has_prev_pages: bool
    has_more_pages: bool
    items: list[int]


@dataclass(frozen=True)
class TitlesBagItemView:
    user_id: int
    titles_bag_id: int
    title: str


@dataclass(frozen=True)
class TitlesBagMenuView(Pageable):
    items: list[TitlesBagItemView]


@dataclass(frozen=True)
class UserContext:
    user_id: int
    chat_id: int
    message_id: int


@dataclass(frozen=True)
class MessageContext(UserContext):
    prev: UserContext | None
    file_id: str | None
    text: str | None


@dataclass(frozen=True)
class CallbackContext(UserContext):
    data: str
    callback_id: str


@dataclass(frozen=True)
class InlineCallbackContext:
    user_id: int
    query: str
    callback_id: str


@dataclass(frozen=True)
class TextTemplate:
    pass


@dataclass(frozen=True)
class UserTemplate(TextTemplate):
    chat_id: int
    user_id: int


@dataclass(frozen=True)
class BoldTemplate(TextTemplate):
    text: str


@dataclass(frozen=True)
class ItalicTemplate(TextTemplate):
    text: str


@dataclass(frozen=True)
class InlineCodeTemplate(TextTemplate):
    text: str


@dataclass(frozen=True)
class Response:
    text_units: str | list[str | TextTemplate]
    markup: InlineKeyboardMarkup | None = None
    picture: BytesIO | None = None

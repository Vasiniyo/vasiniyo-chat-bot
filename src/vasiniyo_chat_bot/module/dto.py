from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from io import BytesIO


@dataclass(frozen=True)
class Payload:
    action: Action
    user_id: int
    genre: AnimeGenre | None = None
    dice_value: int | None = None
    page: int | None = None
    target_id: int | None = None
    title_bag_id: int | None = None


@dataclass(frozen=True)
class UserContext:
    user_id: int
    chat_id: int


@dataclass(frozen=True)
class MessageContext(UserContext):
    message_id: int
    prev: MessageContext | None
    file_id: str | None
    text: str | None


@dataclass(frozen=True)
class CallbackContext(UserContext):
    callback_id: int
    message_id: int | str
    payload: Payload | None


@dataclass(frozen=True)
class InlineCallbackContext:
    callback_id: int
    user_id: int
    chat_id: int
    inline_message_id: str
    payload: Payload | None


@dataclass(frozen=True)
class InlineQueryContext:
    callback_id: str
    user_id: int
    query: str


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
    menu: Menu | None = None
    picture: BytesIO | None = None


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
    GIFT_RECIPIENTS_MENU = "9"
    GIFT_TITLE_MENU = "a"
    GIVE_TITLE = "b"
    OPEN_EXCHANGE_TITLE_MENU = "c"
    EXCHANGE_TITLE = "d"


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
    has_return_button: bool = True


@dataclass(frozen=True)
class LeaderboardRow:
    user_id: int
    value: str | int


@dataclass(frozen=True)
class Leaderboard:
    chat_id: int
    rows: list[LeaderboardRow]


@dataclass(frozen=True)
class Menu: ...


class AnimeGenre(Enum):
    RANDOM = 0
    ACTION = 1
    ADVENTURE = 2
    COMEDY = 3
    DRAMA = 4
    FANTASY = 5
    HORROR = 6
    MYSTERY = 7
    ROMANCE = 8
    SCI_FI = 9
    SLICE = 10
    SPORTS = 11
    THRILLER = 12

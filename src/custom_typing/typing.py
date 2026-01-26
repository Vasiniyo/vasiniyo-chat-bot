from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TypedDict

from telebot.types import CallbackQuery, Message


@dataclass
class Config:
    @dataclass
    class Drinks:
        answer: list[str | None]
        emoji: list[str | None]

    @dataclass
    class Espers:
        answer: list[str | None]
        emoji: list[str | None]

    @dataclass
    class CustomTitles:
        adjectives: list[str]
        nouns: list[str]
        weights: list[int]

    @dataclass
    class LongMessage:
        messages: list[str]
        max_len: int

    @dataclass
    class TriggerReplies:
        sticker_to_sticker: dict[str, list[str]]
        text_to_sticker: dict[str, list[str]]
        text_to_text_to_target: dict[str, list[str]]
        text_to_text: dict[str, list[str]]
        text_to_text_no_fuzzy: dict[str, list[str]]

    @dataclass
    class Captcha:
        @dataclass
        class Gen:
            length: int
            banned_symbols: str
            max_rotation: int
            margins_width: int
            margins_color: str
            font_path: str

        @dataclass
        class Validate:
            timer: int
            update_freq: int
            attempts: int
            bar_length: int

        gen: Gen
        validate: Validate
        content_types: list[str]
        greeting_message: str

    @dataclass
    class Event:
        @dataclass
        class Picture:
            background: Path
            avatar_size: int
            avatar_position_x: int
            avatar_position_y: int

        default_winner_avatar: Path
        winner_pictures: list[Picture]

    triggerReplies: TriggerReplies
    long_message: LongMessage
    custom_titles: CustomTitles
    drinks: list[Drinks]
    espers: list[Espers]
    captcha_properties: Captcha
    event: Event
    language: str
    allowed_chat_ids: list[str]
    mods: list[str]


class Action(Enum):
    ROLL_RANDOM_D6 = "0"
    ROLL_D6 = "1"
    OPEN_RENAME_MENU = "2"
    OPEN_STEAL_MENU = "3"
    STEAL_TITLE = "4"
    OPEN_TITLES_BAG = "5"
    SET_TITLE_BAG = "6"


class Field(Enum):
    ACTION_TYPE = "0"
    USER_ID = "1"
    DICE_VALUE = "2"
    PAGE = "3"
    TARGET_USER_ID = "4"
    TITLE_BAG_ID = "5"


class RollType(Enum):
    ROLL_INSTANT = 1
    ROLL_READY = 2
    GIVE_OLD = 3
    WAIT = 4


class RolledDice(TypedDict):
    value: int
    expected_value: int
    win_values: list[int]
    success: bool


class LogDetails(TypedDict, total=False):
    call: CallbackQuery
    message: Message
    user_id: int
    chat_id: int
    details: str
    roll_type: RollType
    dice: RolledDice

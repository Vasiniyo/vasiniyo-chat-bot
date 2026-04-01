from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path


class WinValue(Enum):
    MAX = auto()
    MIN = auto()
    EXACT = auto()


@dataclass(frozen=True)
class PlayCategory:
    name: str
    units: str
    win_value: WinValue
    ranges: list[tuple[int, int]]
    thresholds: dict[int, list[str]]


@dataclass
class Picture:
    background: Path
    avatar_size: int
    avatar_position_x: int
    avatar_position_y: int


@dataclass
class Event:
    default_winner_avatar: Path
    winner_pictures: list[Picture]
    play_categories: list[PlayCategory]


@dataclass(frozen=True)
class PlayStatus:
    category: PlayCategory
    value: int


@dataclass(frozen=True)
class Winner:
    winner_id: int
    value: int
    first_in_day: bool

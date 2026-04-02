from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class Anime:
    link: str | None


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

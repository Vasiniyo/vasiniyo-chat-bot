from dataclasses import dataclass

from injector import inject


@inject
@dataclass(frozen=True)
class DailySizeSettings:
    labels: list[str]
    sad_emoji: list[str]
    happy_emoji: list[str]


@dataclass(frozen=True)
class DailySizeResult:
    label: str
    daily_size: int
    emoji: str

from dataclasses import dataclass


@dataclass
class Drinks:
    answer: list[str | None]
    emoji: list[str | None]


@dataclass(frozen=True)
class DrinkAdvice:
    advice: str | None

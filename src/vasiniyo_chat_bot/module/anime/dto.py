from dataclasses import dataclass


@dataclass(frozen=True)
class Anime:
    link: str | None

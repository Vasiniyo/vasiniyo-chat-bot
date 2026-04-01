from typing import Protocol


class AnimeProvider(Protocol):
    def next_anime(self, score: int) -> str | None: ...

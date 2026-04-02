from typing import Protocol

from vasiniyo_chat_bot.module.anime.dto import AnimeGenre


class AnimeProvider(Protocol):
    def next_anime(self, score: int, anime_genre: AnimeGenre) -> str | None: ...

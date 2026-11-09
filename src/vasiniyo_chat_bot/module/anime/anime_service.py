from injector import inject

from vasiniyo_chat_bot.module.anime.dto import Anime
from vasiniyo_chat_bot.module.anime.provider.anime_provider import AnimeProvider
from vasiniyo_chat_bot.module.dto import AnimeGenre


@inject
class AnimeService:
    def __init__(self, anime_providers: list[AnimeProvider]):
        self._anime_providers = anime_providers

    def handle_anime(self, score: int, anime_genre: AnimeGenre | None = None) -> Anime:
        anime_genre = anime_genre or AnimeGenre.RANDOM
        for provider in self._anime_providers:
            link = provider.next_anime(score, anime_genre)
            if link:
                return Anime(link)
        return Anime(link=None)

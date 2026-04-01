from vasiniyo_chat_bot.module.anime.anime_provider import AnimeProvider
from vasiniyo_chat_bot.module.anime.dto import Anime


class AnimeService:
    def __init__(self, anime_providers: list[AnimeProvider]):
        self._anime_providers = anime_providers

    def handle_anime(self, score: int) -> Anime:
        for provider in self._anime_providers:
            link = provider.next_anime(score)
            if link:
                return Anime(link)
        return Anime(link=None)

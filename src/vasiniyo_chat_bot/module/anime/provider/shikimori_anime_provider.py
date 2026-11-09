import logging

from injector import inject
import requests

from vasiniyo_chat_bot.module.anime.provider.anime_provider import AnimeProvider
from vasiniyo_chat_bot.module.dto import AnimeGenre
from vasiniyo_chat_bot.safely_bot_utils import safe_wrapper

_logger = logging.getLogger(__name__)


@inject
class ShikimoriAnimeProvider(AnimeProvider):
    @safe_wrapper(default=None)
    def next_anime(
        self, score: int, anime_genre: AnimeGenre = AnimeGenre.RANDOM
    ) -> str | None:
        response = requests.get(
            "https://shikimori.one/api/animes",
            params={"order": "random", "score": score, "limit": 1},
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )
        response.raise_for_status()
        return f"https://shikimori.one{response.json()[0]['url']}"

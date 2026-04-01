import logging

import requests

from vasiniyo_chat_bot.module.anime.anime_provider import AnimeProvider

logger = logging.getLogger(__name__)


class ShikimoriAnimeProvider(AnimeProvider):
    def next_anime(self, score: int) -> str | None:
        try:
            response = requests.get(
                "https://shikimori.one/api/animes",
                params={"order": "random", "score": score, "limit": 1},
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )
            if response.status_code != 200:
                return None
            return f"https://shikimori.one{response.json()[0]['url']}"
        except Exception as e:
            logger.error(e)
            return None

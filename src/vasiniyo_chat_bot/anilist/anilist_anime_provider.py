import logging
import random

import requests

from vasiniyo_chat_bot.module.anime.anime_provider import AnimeProvider

logger = logging.getLogger(__name__)


class AnilistAnimeProvider(AnimeProvider):
    def next_anime(self, score: int) -> str | None:
        try:
            query = (
                "query ($page: Int) {"
                "Page(page: $page, perPage: 1) {"
                f"media(type: ANIME, sort: POPULARITY_DESC, averageScore_greater: {score*10}, isAdult: false)"
                "{siteUrl}}}"
            )
            response = requests.post(
                "https://graphql.anilist.co",
                json={"query": query, "variables": {"page": random.randint(1, 50)}},
                headers={"Content-Type": "application/json"},
            )
            if response.status_code != 200:
                return None
            return response.json()["data"]["Page"]["media"][0]["siteUrl"]
        except Exception as e:
            logger.error(e)
            return None

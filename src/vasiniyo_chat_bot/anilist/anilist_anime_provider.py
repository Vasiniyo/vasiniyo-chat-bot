from functools import lru_cache
import logging
import random

import requests

from vasiniyo_chat_bot.module.anime.anime_provider import AnimeProvider
from vasiniyo_chat_bot.module.anime.dto import AnimeGenre
from vasiniyo_chat_bot.safely_bot_utils import safe_wrapper

logger = logging.getLogger(__name__)


class AnilistAnimeProvider(AnimeProvider):
    _genres = {
        AnimeGenre.ADVENTURE: "Adventure",
        AnimeGenre.ACTION: "Action",
        AnimeGenre.COMEDY: "Comedy",
        AnimeGenre.DRAMA: "Drama",
        AnimeGenre.FANTASY: "Fantasy",
        AnimeGenre.HORROR: "Horror",
        AnimeGenre.MYSTERY: "Mystery",
        AnimeGenre.ROMANCE: "Romance",
        AnimeGenre.SCI_FI: "Sci-Fi",
        AnimeGenre.SLICE: "Slice of Life",
        AnimeGenre.SPORTS: "Sports",
        AnimeGenre.THRILLER: "Thriller",
        AnimeGenre.RANDOM: "Random",
    }

    @safe_wrapper(default=None)
    def next_anime(
        self, score: int, genre: AnimeGenre = AnimeGenre.RANDOM
    ) -> str | None:
        links = self._get_links(score, genre)
        if not links:
            return None
        return random.choice(links)

    @lru_cache
    def _get_links(
        self, score: int, genre: AnimeGenre = AnimeGenre.RANDOM
    ) -> list[str]:
        genre_filter = (
            ""
            if genre == AnimeGenre.RANDOM
            else f'genre_in: ["{self._genres.get(genre)}"]'
        )
        query = (
            "query {"
            "Page(page: 1, perPage: 50) {"
            "media(type: ANIME, sort: POPULARITY_DESC, "
            f"averageScore_greater: {score * 10}, isAdult: false, {genre_filter})"
            "{siteUrl}}}"
        )
        response = requests.post(
            "https://graphql.anilist.co",
            json={"query": query},
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return [media["siteUrl"] for media in response.json()["data"]["Page"]["media"]]

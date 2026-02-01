import random

import requests

import safely_bot_utils as bot


def handle_anime(message):
    query = """
    query ($page: Int) {
        Page(page: $page, perPage: 1) {
            media(type: ANIME, sort: POPULARITY_DESC, averageScore_greater: 75, isAdult: false) {
                siteUrl
            }
        }
    }
    """

    response = requests.post(
        "https://graphql.anilist.co",
        json={"query": query, "variables": {"page": random.randint(1, 50)}},
        headers={"Content-Type": "application/json"},
    )

    if response.status_code == 200:
        anime = response.json()["data"]["Page"]["media"][0]
        bot.reply_to(anime["siteUrl"])(message)
    else:
        bot.reply_to(bot.phrases("anime_failed"))(message)

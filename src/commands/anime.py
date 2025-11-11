import requests

import safely_bot_utils as bot


def handle_anime(message):
    response = requests.get(
        "https://shikimori.one/api/animes",
        params={"order": "random", "score": 8, "limit": 1},
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
    )
    if response.status_code == 200:
        bot.reply_to(f"https://shikimori.one{response.json()[0]['url']}")(message)
    else:
        bot.reply_to(bot.phrases("anime_failed"))(message)

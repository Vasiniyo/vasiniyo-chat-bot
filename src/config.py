import logging
import os

import telebot

from constants import IS_TANENBAUM

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] > %(message)s"
)

api_token = os.environ.get("BOT_API_TOKEN")
chat_id = os.environ.get("ACCESS_ID_GROUP")

if not api_token:
    print("BOT_API_TOKEN is not set")
    exit(1)

if not chat_id:
    print("ACCESS_ID_GROUP is not set")
    exit(1)

bot = telebot.TeleBot(api_token)

unique_file_id = {
    "терпи": "AgADcG4AAiWZuUk",
    "терплю": "AgADw3sAAo8vuUk",
    "накидывай": "AgADumAAAk4okUk",
}

decembrist_stickers = {
    sticker.file_unique_id: sticker.file_id
    for sticker in bot.get_sticker_set("ExneskoroSticky").stickers
}

stickers = {
    sticker_name: decembrist_stickers.get(unique_file_id.get(sticker_name))
    for sticker_name in unique_file_id.keys()
}

templates = {
    "sticker_to_sticker": {
        stickers["терпи"]: stickers["терплю"],
        stickers["накидывай"]: stickers["накидывай"],
    },
    "text_to_text": {
        "соер лучший инженер": "и человек хороший",
        "декабрист отличный инженер": "нет, соер",
        "влад мишустин": "лучший буткемп за 500к",
        IS_TANENBAUM: IS_TANENBAUM,
    },
    "text_to_sticker": {
        "терпи": stickers["терплю"],
        "накидывай накидывай": stickers["накидывай"],
    },
}

import logging
import os

import telebot

from constansts import IS_TANENBAUM

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] > %(message)s"
)

_bot = None
_templates = None
_chat_id = None

def get_bot():
    global _bot, _templates, _chat_id
    if _bot is None:
        api_token = os.environ.get("BOT_API_TOKEN")
        chat_id = os.environ.get("ACCESS_ID_GROUP")
        if not api_token:
            print("BOT_API_TOKEN is not set")
            exit(1)
        if not chat_id:
            print("ACCESS_ID_GROUP is not set")
            exit(1)
        _chat_id = chat_id
        _bot = telebot.TeleBot(api_token)

        unique_file_id = {
            "терпи": "AgADcG4AAiWZuUk",
            "терплю": "AgADw3sAAo8vuUk",
            "накидывай": "AgADumAAAk4okUk",
        }

        decembrist_stickers = {
            sticker.file_unique_id: sticker.file_id
            for sticker in _bot.get_sticker_set("ExneskoroSticky").stickers
        }

        stickers = {
            sticker_name: decembrist_stickers.get(unique_file_id.get(sticker_name))
            for sticker_name in unique_file_id.keys()
        }

        _templates = {
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
    return _bot

def get_templates():
    if _templates is None:
        get_bot()
    return _templates

def get_chat_id():
    if _chat_id is None:
        get_bot()
    return _chat_id

if __name__ == "__main__":
    bot = get_bot()
    templates = get_templates()
    chat_id = get_chat_id()

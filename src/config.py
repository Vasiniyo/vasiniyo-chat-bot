import logging
import os
import telebot

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] > %(message)s"
    )
    return logging.getLogger(__name__)

def init_bot():
    api_token = os.environ.get("BOT_API_TOKEN")
    chat_id = os.environ.get("ACCESS_ID_GROUP")

    if not api_token:
        raise ValueError("BOT_API_TOKEN is not set")
    if not chat_id:
        raise ValueError("ACCESS_ID_GROUP is not set")

    return telebot.TeleBot(api_token)

def load_stickers(bot):
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
        },
        "text_to_sticker": {
            "терпи": stickers["терплю"],
            "накидывай накидывай": stickers["накидывай"],
        },
    }

    return templates

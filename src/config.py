import logging
import os

import telebot
import toml

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] > %(message)s"
)

allowed_chats = os.environ.get("ACCESS_ID_GROUP", "*").split(";")
if len(allowed_chats) == 1 and allowed_chats[0] == "":
    allowed_chats.append("*")

api_token = os.environ.get("BOT_API_TOKEN")
if not api_token:
    print("BOT_API_TOKEN is not set")
    exit(1)

bot = telebot.TeleBot(api_token)

decembrist_stickers = {
    sticker.file_unique_id: sticker.file_id
    for sticker in bot.get_sticker_set("ExneskoroSticky").stickers
}

config = toml.load("config.toml")
captcha_properties = {
    "gen": config["captcha_properties"]["gen"],
    "validate": config["captcha_properties"]["validate"],
}

greeting_message = (
    config.get("welcome_message_for_new_members")
    + "\n\n"
    + config.get("link_to_latest_project")
)

stickers = {
    sticker_name: decembrist_stickers.get(unique_file_id)
    for sticker_name, unique_file_id in config.get("unique_file_id").items()
}

to_list = lambda func: lambda value: (
    list(map(lambda v: func(v), value if isinstance(value, list) else [value]))
)

to_sticker_list = lambda value: to_list(lambda v: stickers[v])(value)


def expand_templates(template_dict: dict) -> dict:
    return {
        req.replace(f"{{{category[0]}}}", value): to_list(lambda x: x)(res)
        for req, res in template_dict.items()
        for category in config.get("categories").items()
        for value in category[1]
    }


sticker_to_sticker = {
    stickers[key]: to_sticker_list(value)
    for key, value in config.get("sticker_to_sticker").items()
}
text_to_sticker = {
    key: to_sticker_list(value) for key, value in config.get("text_to_sticker").items()
}
text_to_text = expand_templates(config.get("text_to_text"))
long_message = config.get("long_message").get("long_message")
MESSAGE_MAX_LEN = config.get("long_message").get("message_max_len")
adjectives = config.get("custom-titles").get("adjectives")
nouns = config.get("custom-titles").get("nouns")
drinks = config.get("drink-or-not")
espers = config.get("how-much-espers")
lang = config.get("lang") or "ru"


def check_mods(handlers):
    res = {}

    for mod in handlers:
        if mod not in config["mods"]:
            logging.warning(f"Module [{mod}] is not included")
        else:
            for key, value in handlers[mod].items():
                res[key] = value

    return res


from locale import locale


def phrases(k, *args):
    global lang
    if lang not in locale:
        lang = "ru"
    if k in locale[lang]:
        return locale[lang][k].format(*args)
    return "Мне нечего тебе сказать..."

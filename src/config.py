import bisect
from dataclasses import dataclass
import logging
import os
from pathlib import Path
import sys

import telebot
import toml


@dataclass
class Config:
    @dataclass
    class Drinks:
        answer: list[str | None]
        emoji: list[str | None]

    @dataclass
    class Espers:
        answer: list[str | None]
        emoji: list[str | None]

    @dataclass
    class CustomTitles:
        adjectives: list[str]
        nouns: list[str]
        weights: list[int]

    @dataclass
    class LongMessage:
        messages: list[str]
        max_len: int

    @dataclass
    class TriggerReplies:
        sticker_to_sticker: dict[str, list[str]]
        text_to_sticker: dict[str, list[str]]
        text_to_text_to_target: dict[str, list[str]]
        text_to_text: dict[str, list[str]]

    @dataclass
    class Captcha:
        @dataclass
        class Gen:
            length: int
            banned_symbols: str
            max_rotation: int
            margins_width: int
            margins_color: str
            font_path: str

        @dataclass
        class Validate:
            timer: int
            update_freq: int
            attempts: int
            bar_length: int

        gen: Gen
        validate: Validate
        content_types: list[str]
        greeting_message: str

    @dataclass
    class Event:
        @dataclass
        class Picture:
            background: Path
            avatar_size: int
            avatar_position_x: int
            avatar_position_y: int

        default_winner_avatar: Path
        winner_pictures: list[Picture]

    triggerReplies: TriggerReplies
    long_message: LongMessage
    custom_titles: CustomTitles
    drinks: list[Drinks]
    espers: list[Espers]
    captcha_properties: Captcha
    event: Event
    language: str
    allowed_chat_ids: list[str]
    mods: list[str]


def expand_templates(template_dict: dict) -> dict:
    return {
        req.replace(f"{{{category[0]}}}", value): _to_list(lambda x: x)(res)
        for req, res in template_dict.items()
        for category in _toml_config.get("categories").items()
        for value in category[1]
    }


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] > %(message)s"
)

_allowed_chats = os.environ.get("ACCESS_ID_GROUP", "*").split(";")
if len(_allowed_chats) == 1 and _allowed_chats[0] == "":
    _allowed_chats.append("*")

_api_token = os.environ.get("BOT_API_TOKEN")
if not _api_token:
    print("BOT_API_TOKEN is not set")
    exit(1)

bot = telebot.TeleBot(_api_token)

_toml_config = toml.load("config.toml")
_unique_ids = _toml_config.get("unique_file_id", {})
_sticker_pack_names = {unique_id.split(";")[0] for unique_id in _unique_ids.values()}

# Add test modules if in test mode
TEST_MODE = "--test" in sys.argv or os.environ.get("TEST_MODE", "").lower() == "true"
if TEST_MODE and "test_new_category" not in _toml_config["mods"]:
    _toml_config["mods"].append("test_new_category")
    logging.info("Test mode enabled - adding test modules")
captcha_properties = {
    "gen": _toml_config["captcha_properties"]["gen"],
    "validate": _toml_config["captcha_properties"]["validate"],
    # types of content that the captcha will intercept as a check on the user's answer
    "content_types": _toml_config["captcha_properties"].get("content_types", ["text"]),
}
captcha_content_types = captcha_properties["content_types"]


def get_sticker_set(pack):
    try:
        return bot.get_sticker_set(pack).stickers
    except Exception:
        logging.exception(f"Failed to get sticker set for pack: {pack}")
        return []


stickers_by_unique_id = {
    f"{pack};{sticker.file_unique_id}": sticker.file_id
    for pack in _sticker_pack_names
    for sticker in get_sticker_set(pack)
}

_stickers = {
    sticker_name: stickers_by_unique_id.get(uid)
    for sticker_name, uid in _unique_ids.items()
}

_to_list = lambda func: lambda value: (
    list(map(lambda v: func(v), value if isinstance(value, list) else [value]))
)

_to_sticker_list = lambda value: _to_list(lambda v: _stickers[v])(value)
_captcha_properties = _toml_config.get("captcha_properties", {})

_adjectives = sorted(
    set([str(x) for x in _toml_config.get("custom-titles", {}).get("adjectives", [])]),
    key=len,
)
_nouns = list(set(_toml_config.get("custom-titles", {}).get("nouns", [])))
_weights = []

for adj in _adjectives:
    max_len = 15 - len(adj)
    count = bisect.bisect_right([len(n) for n in _nouns], max_len)
    _weights.append(count)

config = Config(
    triggerReplies=Config.TriggerReplies(
        sticker_to_sticker={
            _stickers[key]: _to_sticker_list(value)
            for key, value in _toml_config.get("sticker_to_sticker", {}).items()
        },
        text_to_sticker={
            key: _to_sticker_list(value)
            for key, value in _toml_config.get("text_to_sticker", {}).items()
        },
        text_to_text_to_target=expand_templates(
            _toml_config.get("text_to_text_to_target", {})
        ),
        text_to_text=expand_templates(_toml_config.get("text_to_text", {})),
    ),
    long_message=Config.LongMessage(
        messages=_toml_config.get("long_message", {}).get("long_message", []),
        max_len=_toml_config.get("long_message", {}).get("message_max_len", 1000),
    ),
    custom_titles=Config.CustomTitles(
        adjectives=_adjectives, nouns=_nouns, weights=_weights
    ),
    drinks=list(
        map(
            lambda cfg: Config.Drinks(
                answer=cfg.get("answer", []), emoji=cfg.get("emoji", [])
            ),
            _toml_config.get("drink-or-not", {}),
        )
    ),
    espers=list(
        map(
            lambda cfg: Config.Espers(
                answer=cfg.get("answer", []), emoji=cfg.get("emoji", [])
            ),
            _toml_config.get("how-much-espers", {}),
        )
    ),
    captcha_properties=Config.Captcha(
        gen=Config.Captcha.Gen(
            length=_captcha_properties.get("gen", {}).get("length", 5),
            banned_symbols=_captcha_properties.get("gen", {}).get(
                "banned_symbols", "104aqiol"
            ),
            max_rotation=_captcha_properties.get("gen", {}).get("max_rotation", 45),
            margins_width=_captcha_properties.get("gen", {}).get("margins_width", 12),
            margins_color=_captcha_properties.get("gen", {}).get(
                "margins_color", "#0e1621"
            ),
            font_path=_captcha_properties.get("gen", {}).get(
                "font_path", "/usr/share/fonts/TTF/GoMonoNerdFontMono-Regular.ttf"
            ),
        ),
        validate=Config.Captcha.Validate(
            timer=_captcha_properties.get("validate", {}).get("timer", 90),
            update_freq=_captcha_properties.get("validate", {}).get("update_freq", 10),
            attempts=_captcha_properties.get("validate", {}).get("attempts", 5),
            bar_length=_captcha_properties.get("validate", {}).get("bar_length", 20),
        ),
        # types of content that the captcha will intercept as a check on the user's answer
        content_types=_captcha_properties.get("content_types", ["text"]),
        # content_types = tomlConfig["captcha_properties"].get("content_types", ["text"]),
        greeting_message=(
            _toml_config.get(
                "welcome_message_for_new_members", "Добро пожаловать в чат!"
            )
            + "\n\n"
            + _toml_config.get(
                "link_to_latest_project",
                "https://github.com/Vasiniyo/vasiniyo-chat-bot",
            )
        ),
    ),
    event=Config.Event(
        default_winner_avatar=(
            Path(__file__).parent
            / "assets"
            / _toml_config.get("event", {}).get("default_winner_avatar", "anon-ava.jpg")
        ),
        winner_pictures=[
            Config.Event.Picture(
                background=Path(__file__).parent
                / "assets"
                / cfg.get("background", "wanted-template.png"),
                avatar_size=cfg.get("avatar_size", 380),
                avatar_position_x=cfg.get("avatar_position_x", 150),
                avatar_position_y=cfg.get("avatar_position_y", 320),
            )
            for cfg in _toml_config.get("event", {}).get("winner_pictures", [{}])
        ],
    ),
    language=_toml_config.get("lang", "ru"),
    allowed_chat_ids=_allowed_chats,
    mods=_toml_config.get(
        "mods",
        [
            "core",
            "anime",
            "event",
            "likes",
            "play",
            "roll_title",
            "drink_or_not",
            "reply",
            "captcha",
            "long_message",
        ],
    ),
)

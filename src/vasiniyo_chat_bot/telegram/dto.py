from enum import Enum


class Action(Enum):
    ROLL_RANDOM_D6 = "0"
    ROLL_D6 = "1"
    OPEN_RENAME_MENU = "2"
    OPEN_STEAL_MENU = "3"
    STEAL_TITLE = "4"
    OPEN_TITLES_BAG = "5"
    SET_TITLE_BAG = "6"
    CAPTCHA_UPDATE = "7"
    ANIME = "8"


class Field(Enum):
    ACTION_TYPE = "0"
    USER_ID = "1"
    DICE_VALUE = "2"
    PAGE = "3"
    TARGET_USER_ID = "4"
    TITLE_BAG_ID = "5"
    ANIME_GENRE = "6"

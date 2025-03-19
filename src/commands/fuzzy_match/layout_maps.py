ENG_TO_RU = {
    "q": "й",
    "w": "ц",
    "e": "у",
    "r": "к",
    "t": "е",
    "y": "н",
    "u": "г",
    "i": "ш",
    "o": "щ",
    "p": "з",
    "a": "ф",
    "s": "ы",
    "d": "в",
    "f": "а",
    "g": "п",
    "h": "р",
    "j": "о",
    "k": "л",
    "l": "д",
    "z": "я",
    "x": "ч",
    "c": "с",
    "v": "м",
    "b": "и",
    "n": "т",
    "m": "ь",
}
# Reverse mapping: Russian to English (for lowercase)
RU_TO_ENG = {v: k for k, v in ENG_TO_RU.items()}

# Create mappings for uppercase letters
ENG_TO_RU_UPPER = {k.upper(): v.upper() for k, v in ENG_TO_RU.items()}
RU_TO_ENG_UPPER = {k.upper(): v.upper() for k, v in RU_TO_ENG.items()}

LAYOUT_MAP = {**ENG_TO_RU, **ENG_TO_RU_UPPER, **RU_TO_ENG, **RU_TO_ENG_UPPER}

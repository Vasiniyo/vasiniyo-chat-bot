import random

from rapidfuzz import fuzz, process


def find_best_match(input_text: str, category_keys: list, simmilarity=80):
    if result := process.extractOne(input_text, category_keys, scorer=fuzz.ratio):
        best_match, score, _ = result
        if score >= (simmilarity):
            return best_match
    return input_text


def choice_one_match(user_message, category_keys):
    words = user_message.split()
    good_words = list(
        filter(
            lambda m: m[0] is not None,
            [
                test_match(substring, category_keys)
                for substring in [
                    " ".join(words[i : j + 1])
                    for i in range(len(words))
                    for j in range(i, len(words))
                ]
            ],
        )
    )
    return (None, False) if len(good_words) == 0 else random.choice(good_words)


def test_match(user_message: str, category_keys: list):
    """
    Returns (key, is_inverted) if found, otherwise (None, False).
    """
    user_message = user_message.lower()
    lower_category_keys = list(map(lambda k: k.lower(), category_keys))
    matched = [
        (find_best_match(user_message, lower_category_keys), False),
        (find_best_match(__convert_layout(user_message), lower_category_keys), True),
    ]
    return next(filter(lambda m: m[0] in lower_category_keys, matched), (None, False))


def __convert_layout(text: str) -> str:
    return "".join(LAYOUT_MAP.get(char, char) for char in text)


LAYOUT_MAP = dict(
    zip(
        "qwertyuiopasdfghjklzxcvbnmйцукенгшщзфывапролдячсмить",
        "йцукенгшщзфывапролдячсмитьqwertyuiopasdfghjklzxcvbnm",
    )
)

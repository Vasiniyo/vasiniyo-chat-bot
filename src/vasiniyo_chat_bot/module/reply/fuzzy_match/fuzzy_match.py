from itertools import zip_longest
import random

from rapidfuzz import fuzz


def find_best_match(input_text: str, match_key: list, simmilarity=80):
    match_key = match_key[0] if match_key else None
    match_simmilarity = fuzz.partial_ratio(match_key, input_text)

    if match_simmilarity >= simmilarity:
        return match_key
    return input_text


def find_matches(input_text: str, category_keys: list, simmilarity=80):
    words = input_text.split()
    match_keys = []

    for key in category_keys:
        key_len = len(key.split())
        max_ratio = 0

        for i in range(len(words) - key_len + 1):
            substring = " ".join(words[i : i + key_len])
            max_ratio = max(max_ratio, fuzz.ratio(key, substring))

        if max_ratio >= simmilarity:
            match_keys.append(key)

    return match_keys


def choice_one_match(user_message, category_keys):
    good_words = list(
        filter(lambda m: m[0] is not None, test_match(user_message, category_keys))
    )
    return (None, False) if len(good_words) == 0 else random.choice(good_words)


def test_match(user_message: str, category_keys: list):
    """
    Returns (key, is_inverted) if found, otherwise (None, False).
    """
    user_message = user_message.lower()
    lower_category_keys = list(map(lambda k: k.lower(), category_keys))
    matched = [
        *zip_longest(
            find_matches(user_message, lower_category_keys), "", fillvalue=False
        ),
        *zip_longest(
            find_matches(__convert_layout(user_message), lower_category_keys),
            "",
            fillvalue=True,
        ),
    ]
    return matched or [(None, False)]


def __convert_layout(text: str) -> str:
    return "".join(LAYOUT_MAP.get(char, char) for char in text)


LAYOUT_MAP = dict(
    zip(
        "qwertyuiopasdfghjklzxcvbnmйцукенгшщзфывапролдячсмить",
        "йцукенгшщзфывапролдячсмитьqwertyuiopasdfghjklzxcvbnm",
    )
)

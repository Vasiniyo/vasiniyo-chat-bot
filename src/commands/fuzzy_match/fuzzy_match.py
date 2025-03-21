from rapidfuzz import fuzz, process


def find_best_match(input_text: str, category_keys: list, simmilarity=80):
    if result := process.extractOne(input_text, category_keys, scorer=fuzz.ratio):
        best_match, score, _ = result
        if score >= (simmilarity):
            return best_match
    return input_text


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

from rapidfuzz import fuzz, process

from config import templates

from .layout_maps import LAYOUT_MAP


def find_best_match(input_text: str, templates: dict, simmilarity=80):
    if not input_text or not templates:
        return None

    result = process.extractOne(input_text, templates.keys(), scorer=fuzz.ratio)
    if result:
        best_match, score, _ = result
        if score >= (simmilarity):
            return best_match
    return input_text


def test_match(user_message: str, category: str):
    """
    Returns (True, key, is_inverted) if found, otherwise (False, None, False).
    """
    inverted_user_message = __convert_layout(user_message)

    matched_original = find_best_match(user_message, templates[category])
    matched_inverted = find_best_match(inverted_user_message, templates[category])

    if matched_original and matched_original in templates[category]:
        return True, matched_original, False
    elif matched_inverted and matched_inverted in templates[category]:
        return True, matched_inverted, True

    return False, None, False


def __convert_layout(text: str) -> str:
    return "".join(LAYOUT_MAP.get(char, char) for char in text)

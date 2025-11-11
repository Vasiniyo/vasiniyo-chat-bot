"""Utility functions for the play command."""

import datetime
import random

from .play import PlayableCategory
from .play_config import CATEGORIES


def get_current_playable_category(chat_id: int, test: bool = False) -> PlayableCategory:
    today = datetime.date.today()

    # TODO redo with proper handler for test case
    if not test:
        seed = hash((chat_id, today.year, today.month, today.day))
    else:
        seed = random.randint(0, 2**32 - 1)

    rng = random.Random(seed)
    category_names = list(CATEGORIES.keys())
    selected_name = rng.choice(category_names)

    return CATEGORIES[selected_name]


def get_player_value(category: PlayableCategory, chat_id: int, user_id: int) -> int:
    today = datetime.date.today()
    seed = hash((user_id, chat_id, today.year, today.month, today.day, category.name))

    return category.get_random_value(seed)

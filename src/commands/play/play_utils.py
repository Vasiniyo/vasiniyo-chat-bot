import datetime
import logging
import random
from typing import Optional

from .play import PlayableCategory
from .play_config import CATEGORIES

logger = logging.getLogger(__name__)

_current_category: Optional[PlayableCategory] = None
_last_category_date: Optional[datetime.date] = None


def get_current_playable_category(
    chat_id: int, test: bool = False, force_refresh: bool = False
) -> PlayableCategory:
    global _current_category, _last_category_date

    today = datetime.date.today()

    should_refresh = (
        force_refresh
        or _current_category is None
        or _last_category_date != today
        or test
    )

    if not should_refresh and not test and _current_category is not None:
        logger.debug(f"Using cached category: {_current_category.name}")
        return _current_category

    if not test:
        seed = hash((chat_id, today.year, today.month, today.day))
        logger.info(f"Daily category rotation - Date: {today}, Seed: {seed}")
    else:
        seed = random.randint(0, 2**32 - 1)
        logger.info(f"TEST MODE: Random category - Seed: {seed}")

    rng = random.Random(seed)
    category_names = [name for name, cat in CATEGORIES.items() if cat is not None]
    selected_name = rng.choice(category_names)
    selected_category = CATEGORIES[selected_name]

    if selected_category is None:
        raise RuntimeError(f"Category '{selected_name}' failed to load")

    if not test:
        _current_category = selected_category
        _last_category_date = today
        logger.info(f"Selected category for today: '{selected_name}'")
    else:
        logger.info(f"TEST: Selected random category: '{selected_name}'")

    return selected_category


def get_cached_category() -> Optional[PlayableCategory]:
    return _current_category


def should_refresh_category() -> bool:
    global _last_category_date

    if _last_category_date is None:
        return True

    today = datetime.date.today()
    return _last_category_date != today


def force_category_refresh(chat_id: int) -> PlayableCategory:
    logger.info("Forcing category refresh...")
    category = get_current_playable_category(chat_id, force_refresh=True)
    if category is None:
        raise RuntimeError("Failed to refresh category")
    return category


def get_player_value(category: PlayableCategory, chat_id: int, user_id: int) -> int:
    today = datetime.date.today()
    seed = hash((user_id, chat_id, today.year, today.month, today.day, category.name))

    return category.get_random_value(seed)

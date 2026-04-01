import datetime
from functools import wraps
import json
import logging
from typing import Callable, ParamSpec, TypeVar

from vasiniyo_chat_bot.telegram.dto import Field

P = ParamSpec("P")
R = TypeVar("R")

logger = logging.getLogger(__name__)


def safe_wrapper(
    default: R | None = None, message: str = "Exception occurred"
) -> Callable[[Callable[P, R]], Callable[P, R | None]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R | None]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
            try:
                return func(*args, **kwargs)
            except:
                logger.exception(message)
                return default

        return wrapper

    return decorator


@safe_wrapper(default=None)
def extract_field(payload: dict[str, int | str], field: Field):
    if str(payload.get(field.value)).lstrip("-").isdigit():
        return int(payload.get(field.value))
    return None


@safe_wrapper(default={})
def parse_json(data: str) -> dict:
    return json.loads(data)


@safe_wrapper(default=0)
def daily_hash(salt: int) -> int:
    """
    https://gist.github.com/badboy/6267743
    """
    key = salt + datetime.date.today().toordinal()
    key = (key ^ 61) ^ (key >> 16)
    key = key + (key << 3)
    key = key ^ (key >> 4)
    key = key * 0x27D4EB2D
    key = key ^ (key >> 15)
    return key

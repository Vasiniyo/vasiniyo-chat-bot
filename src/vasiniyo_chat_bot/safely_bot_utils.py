import datetime
from functools import wraps
import json
import logging
import time
from typing import Callable
from typing import TypeVar

from telebot.apihelper import ApiTelegramException

from vasiniyo_chat_bot.module.dto import Field

_logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., object])


def safe_wrapper(
    default: object, message: str = "Exception occurred"
) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ApiTelegramException as e:
                retry_after = e.result_json.get("parameters", {}).get(
                    "retry_after", None
                )
                if retry_after is not None:
                    _logger.warning(
                        f"Too Many Requests. Retrying after {retry_after}s."
                    )
                    time.sleep(retry_after + 1)
                    try:
                        return func(*args, **kwargs)
                    except:
                        _logger.exception(message)
                        return default
            except:
                _logger.exception(message)
                return default

        return wrapper

    return decorator


@safe_wrapper(default=None)
def extract_field(payload: dict[str, int | str], field: Field):
    value = str(payload.get(field.value)).lstrip("-")
    if value.isdigit():
        return int(value)
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

from functools import wraps
import logging

logger = logging.getLogger(__name__)


def log_handler(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        logger.info(
            "Handler: %s | User: [%s, %s] | Message type: %s",
            func.__name__,
            message.from_user.id,
            message.from_user.username,
            message.content_type,
        )
        return func(message, *args, **kwargs)

    return wrapper

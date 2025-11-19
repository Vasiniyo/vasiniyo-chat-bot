from datetime import datetime
import json
import logging
import traceback
from typing import Optional

from telebot.types import CallbackQuery, Chat, Message, User

from custom_typing.typing import LogDetails


def _pretty_msg(arg):
    if getattr(arg, "message_id", False):
        return _message_info(arg)
    return arg


def _pretty_markup(arg):
    if getattr(arg, "keyboard", False):
        handle_row = lambda l: map(lambda b: f"[{b.text}]", l)
        handle_column = map(lambda l: " ".join(handle_row(l)), arg.keyboard)
        return "buttons{ (" + ") (".join(handle_column) + ") }"
    return arg


def logger(func):
    def wrapper(*args, **kwargs):
        def to_serializable(arg):
            return json.loads(
                json.dumps(
                    arg,
                    default=lambda obj: {
                        "type": f"{type(obj).__module__}.{type(obj).__name__}",
                        "repr": repr(obj),
                    },
                )
            )

        try:
            pretty_args = [to_serializable(_pretty_msg(arg)) for arg in args]
            pretty_kwargs = {
                k: to_serializable(_pretty_markup(v))
                for i, (k, v) in enumerate(kwargs.items())
            }
            extra = {
                "details": {"details": {"args": pretty_args, "kwargs": pretty_kwargs}}
            }
        except Exception as e:
            extra = {}
            get_json_logger().exception(e)
        get_json_logger().info(f"func_call_{func.__name__}", extra=extra)
        return func(*args, **kwargs)

    return wrapper


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_object = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "location": {
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            },
            "exception": record.exc_info
            and {
                "error_type": record.exc_info[0].__name__,
                "stacktrace": traceback.format_exception(
                    *record.exc_info, limit=None, chain=True
                ),
            },
            "details": getattr(record, "extra_data", {}).get("details"),
        }
        return f"{json.dumps(log_object, ensure_ascii=False)}\n"


class AutoContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        details: Optional[LogDetails] = getattr(record, "details", None)
        if not details:
            return True
        context = {
            key: value
            for key, value in {
                "call": _call_info(details.get("call")),
                "message": _message_info(details.get("message")),
                "chat_id": details.get("chat_id"),
                "user_id": details.get("user_id"),
                "details": details.get("details"),
                "roll_type": details.get("roll_type")
                and {
                    "name": details.get("roll_type").name,
                    "value": details.get("roll_type").value,
                },
                "dice": details.get("dice"),
            }.items()
            if value is not None
        }
        record.extra_data = {"details": context}
        return True


def _call_info(call: Optional[CallbackQuery]) -> Optional[dict]:
    return call and {
        "from_user": _user_info(call.from_user),
        "chat": _chat_info(call.message.chat),
        "message": _message_info(call.message),
        "data": call.data,
    }


def _message_info(message: Optional[Message]) -> Optional[dict]:
    return message and {
        "id": message.id,
        "content_type": message.content_type,
        "text": message.text,
        "from_user": _user_info(message.from_user),
    }


def _user_info(user: Optional[User]) -> Optional[dict]:
    return user and {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_bot": user.is_bot,
    }


def _chat_info(chat: Optional[Chat]) -> Optional[dict]:
    return chat and {"id": chat.id, "title": chat.title, "type": chat.type}


json_logger = logging.getLogger("json_logger")
json_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
handler.addFilter(AutoContextFilter())
json_logger.addHandler(handler)
json_logger.propagate = False


def get_json_logger():
    return json_logger

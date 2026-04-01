from enum import Enum
import logging
import traceback
from typing import TypedDict

from telebot.types import CallbackQuery, Chat, Message, User


class RollType(Enum):
    ROLL_INSTANT = 1
    ROLL_READY = 2
    GIVE_OLD = 3
    WAIT = 4


class RolledDice(TypedDict):
    value: int
    expected_value: int
    win_values: list[int]
    success: bool


class LogDetails(TypedDict, total=False):
    call: CallbackQuery
    message: Message
    user_id: int
    chat_id: int
    details: str
    roll_type: RollType
    dice: RolledDice


class LogFormatter(logging.Formatter):
    def format(self, record):
        extras = []
        for k, v in record.__dict__.items():
            if k not in (
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "taskName",
            ):
                match k:
                    case "tg_call":
                        if isinstance(v, CallbackQuery):
                            extras.append(f"chat_id={v.message.chat.id!r}")
                            extras.append(f"call_id={v.id!r}")
                            extras.append(f"call_data={v.data!r}")
                            extras.append(f"message_id={v.message.id!r}")
                            extras.append(f"user_id={v.from_user.id!r}")
                            if record.levelno != logging.INFO:
                                extras.append(f"chat_id={v.message.chat.id!r}")
                                extras.append(f"chat_title={v.message.chat.title!r}")
                                extras.append(f"chat_type={v.message.chat.type!r}")
                                extras.append(f"message_text={v.message.text!r}")
                                extras.append(f"username={v.from_user.username}")
                                extras.append(f"first_name={v.from_user.first_name}")
                                extras.append(f"last_name={v.from_user.last_name}")
                                extras.append(f"is_bot={v.from_user.is_bot}")
                    case "tg_message":
                        if isinstance(v, Message):
                            extras.append(f"message_id={v.id!r}")
                            extras.append(f"content_type={v.content_type!r}")
                            extras.append(f"user_id={v.from_user.id!r}")
                            if record.levelno != logging.INFO:
                                extras.append(f"chat_id={v.chat.id!r}")
                                extras.append(f"chat_title={v.chat.title!r}")
                                extras.append(f"chat_type={v.chat.type!r}")
                                extras.append(f"message_text={v.text!r}")
                                extras.append(f"username={v.from_user.username}")
                                extras.append(f"first_name={v.from_user.first_name}")
                                extras.append(f"last_name={v.from_user.last_name}")
                                extras.append(f"is_bot={v.from_user.is_bot}")
                    case _:
                        extras.append(f"{k}={v!r}")
        extras = " ".join(extras)
        trace = ""
        if record.exc_info:
            trace = "\n" + "".join(traceback.format_exception(*record.exc_info)).rstrip(
                "\n"
            )
        level = record.levelname
        message = record.getMessage()
        time = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        module = record.name
        return f"{time} {level} - {module} > msg={message!r} {extras}{trace}"

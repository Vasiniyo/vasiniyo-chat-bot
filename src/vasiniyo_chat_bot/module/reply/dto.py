from dataclasses import dataclass
from enum import Enum
from enum import auto


class MessageType(Enum):
    TEXT = auto()
    STICKER = auto()


@dataclass(frozen=True)
class Trigger:
    response_type: MessageType
    request: str
    responses: list[str]
    chance: float
    to_target: bool
    fuzzy: bool
    exact_match: bool


@dataclass(frozen=True)
class StickerTrigger(Trigger): ...


@dataclass(frozen=True)
class TextTrigger(Trigger): ...


@dataclass(frozen=True)
class TriggerReplies:
    text_replies: list[TextTrigger]
    sticker_replies: list[StickerTrigger]


@dataclass
class LongMessage:
    responses: list[str]
    max_len: int


@dataclass(frozen=True)
class StickerResult:
    file_id: str
    to_reply: bool


@dataclass(frozen=True)
class TextResult:
    text: str
    to_reply: bool

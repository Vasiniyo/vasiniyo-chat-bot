from dataclasses import dataclass
from enum import Enum, auto


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


@dataclass(frozen=True)
class StickerTrigger(Trigger):
    fuzzy: False = False


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


@dataclass(frozen=True)
class TextResult:
    text: str
    to_reply: bool

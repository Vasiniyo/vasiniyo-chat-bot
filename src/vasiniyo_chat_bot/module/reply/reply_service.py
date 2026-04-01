import math
import random

from .dto import (
    LongMessage,
    MessageType,
    StickerResult,
    TextResult,
    Trigger,
    TriggerReplies,
)
from .fuzzy_match.fuzzy_match import choice_one_match


class ReplyService:
    def __init__(self, long_messages: LongMessage, triggers: TriggerReplies) -> None:
        self._long_message_settings = long_messages
        self._text_triggers = triggers.text_replies
        self._sticker_triggers = triggers.sticker_replies

    def handle_text_replies(self, text: str) -> TextResult | StickerResult | None:
        if self._is_long_message(text):
            reply = random.choice(self._long_message_settings.responses)
            return TextResult(text=reply, to_reply=False)
        return self._get_reply(text, self._text_triggers)

    def handle_sticker_replies(self, file_id: str) -> TextResult | StickerResult | None:
        return self._get_reply(file_id, self._sticker_triggers)

    @staticmethod
    def _get_reply(text, triggers: list[Trigger]) -> TextResult | StickerResult | None:
        possible_replies = []
        for trigger in triggers:
            if trigger.chance < random.random():
                continue
            if not trigger.fuzzy and text == trigger.request:
                reply = random.choice(trigger.responses)
            else:
                answers = {trigger.request: trigger.responses}
                matched_key, used_inverted = choice_one_match(text, answers.keys())
                reply = random.choice(answers.get(matched_key) or [None])
                if trigger.response_type == MessageType.TEXT and used_inverted:
                    reply = f"{matched_key}?\n{reply}"
            if not reply:
                continue
            if trigger.response_type == MessageType.TEXT:
                possible_replies.append(
                    TextResult(text=reply, to_reply=trigger.to_target)
                )
            else:
                possible_replies.append(StickerResult(file_id=reply))
        if possible_replies:
            return random.choice(possible_replies)
        return None

    def _is_long_message(self, text: str) -> bool:
        return (
            random.random() < self.laplace_cdf(len(text))
            and len(text) >= self._long_message_settings.max_len
        )

    def laplace_cdf(self, x: int) -> float:
        # scales values between 0 and maximal allowed message length in telegram
        scale = lambda a: a / 4096
        l = scale(self._long_message_settings.max_len / 2)
        m = scale(self._long_message_settings.max_len * 2)
        x = scale(x)
        if x < m:
            return 0.5 * math.e ** ((x - m) / l)
        return 1.0 - 0.5 / math.e ** ((x - m) / l)

from dataclasses import dataclass
import json

from vasiniyo_chat_bot.module.dto import Action
from vasiniyo_chat_bot.module.dto import Field
from vasiniyo_chat_bot.safely_bot_utils import extract_field
from vasiniyo_chat_bot.safely_bot_utils import parse_json


@dataclass(frozen=True)
class CaptchaPayload:
    action: Action
    user_id: int


class CaptchaPayloadFactory:
    _valid_payload_actions = {Action.CAPTCHA_UPDATE.value}

    @staticmethod
    def has_captcha_payload(data: str) -> bool:
        payload = parse_json(data)
        return (
            payload.get(Field.ACTION_TYPE.value)
            in CaptchaPayloadFactory._valid_payload_actions
        )

    @staticmethod
    def get_payload(data: str) -> CaptchaPayload:
        payload = parse_json(data)
        action_value = payload.get(Field.ACTION_TYPE.value)
        action = Action._value2member_map_.get(action_value)
        return CaptchaPayload(
            action=action if isinstance(action, Action) else None,
            user_id=extract_field(payload, Field.USER_ID),
        )

    @staticmethod
    def update_captcha(user_id: int) -> str:
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.CAPTCHA_UPDATE.value,
                Field.USER_ID.value: user_id,
            }
        )

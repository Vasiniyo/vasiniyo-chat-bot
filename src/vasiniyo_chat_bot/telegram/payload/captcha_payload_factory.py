import json

from vasiniyo_chat_bot.safely_bot_utils import parse_json
from vasiniyo_chat_bot.telegram.dto import Action, Field


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
    def update_captcha(user_id: int) -> str:
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.CAPTCHA_UPDATE.value,
                Field.USER_ID.value: user_id,
            }
        )

from dataclasses import dataclass
import json

from vasiniyo_chat_bot.module.dto import Action
from vasiniyo_chat_bot.module.dto import Field
from vasiniyo_chat_bot.safely_bot_utils import extract_field
from vasiniyo_chat_bot.safely_bot_utils import parse_json


@dataclass(frozen=True)
class TitlesPayload:
    action: Action
    user_id: int
    dice_value: int | None = None
    page: int | None = None
    target_id: int | None = None
    title_bag_id: int | None = None


class TitlesPayloadFactory:
    _valid_payload_actions = {
        Action.ROLL_RANDOM_D6.value,
        Action.ROLL_D6.value,
        Action.OPEN_RENAME_MENU.value,
        Action.OPEN_STEAL_MENU.value,
        Action.STEAL_TITLE.value,
        Action.OPEN_TITLES_BAG.value,
        Action.SET_TITLE_BAG.value,
        Action.GIFT_RECIPIENTS_MENU.value,
        Action.GIFT_TITLE_MENU.value,
        Action.GIVE_TITLE.value,
    }

    @staticmethod
    def has_titles_payload(data: str) -> bool:
        payload = parse_json(data)
        return (
            payload.get(Field.ACTION_TYPE.value)
            in TitlesPayloadFactory._valid_payload_actions
        )

    @staticmethod
    def get_payload(data: str) -> TitlesPayload:
        payload = parse_json(data)
        action_value = payload.get(Field.ACTION_TYPE.value)
        action = Action._value2member_map_.get(action_value)
        return TitlesPayload(
            action=action if isinstance(action, Action) else None,
            user_id=extract_field(payload, Field.USER_ID),
            dice_value=extract_field(payload, Field.DICE_VALUE),
            page=extract_field(payload, Field.PAGE),
            target_id=extract_field(payload, Field.TARGET_USER_ID),
            title_bag_id=extract_field(payload, Field.TITLE_BAG_ID),
        )

    @staticmethod
    def titles_bag_menu(page: int, user_id: int) -> str:
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.OPEN_TITLES_BAG.value,
                Field.USER_ID.value: user_id,
                Field.PAGE.value: page,
            }
        )

    @staticmethod
    def set_title_bag(title_bag_id: int, user_id: int) -> str:
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.SET_TITLE_BAG.value,
                Field.USER_ID.value: user_id,
                Field.TITLE_BAG_ID.value: title_bag_id,
            }
        )

    @staticmethod
    def d6(i, user_id: int) -> str:
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.ROLL_D6.value,
                Field.USER_ID.value: user_id,
                Field.DICE_VALUE.value: i,
            }
        )

    @staticmethod
    def random_d6(user_id: int) -> str:
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.ROLL_RANDOM_D6.value,
                Field.USER_ID.value: user_id,
            }
        )

    @staticmethod
    def rename_menu(user_id: int) -> str:
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.OPEN_RENAME_MENU.value,
                Field.USER_ID.value: user_id,
            }
        )

    @staticmethod
    def steal_menu(page: int, user_id: int) -> str:
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.OPEN_STEAL_MENU.value,
                Field.USER_ID.value: user_id,
                Field.PAGE.value: page,
            }
        )

    @staticmethod
    def steal_title(title_id: int, target_id: int, user_id: int) -> str:
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.STEAL_TITLE.value,
                Field.USER_ID.value: user_id,
                Field.TITLE_BAG_ID.value: title_id,
                Field.TARGET_USER_ID.value: target_id,
            }
        )

    @staticmethod
    def gift_recipients_menu(page: int, user_id: int) -> str:
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.GIFT_RECIPIENTS_MENU.value,
                Field.USER_ID.value: user_id,
                Field.PAGE.value: page,
            }
        )

    @staticmethod
    def gift_titles_menu(page: int, target_id: int, user_id: int) -> str:
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.GIFT_TITLE_MENU.value,
                Field.USER_ID.value: user_id,
                Field.TARGET_USER_ID.value: target_id,
                Field.PAGE.value: page,
            }
        )

    @staticmethod
    def give_title(title_id: int, target_id: int, user_id: int):
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.GIVE_TITLE.value,
                Field.USER_ID.value: user_id,
                Field.TARGET_USER_ID.value: target_id,
                Field.TITLE_BAG_ID.value: title_id,
            }
        )

    @staticmethod
    def empty():
        return json.dumps({})

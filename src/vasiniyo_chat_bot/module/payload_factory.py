import json

from vasiniyo_chat_bot.module.dto import Action
from vasiniyo_chat_bot.module.dto import AnimeGenre
from vasiniyo_chat_bot.module.dto import Field
from vasiniyo_chat_bot.module.dto import Payload
from vasiniyo_chat_bot.safely_bot_utils import parse_json


class PayloadFactory:
    @staticmethod
    def dump(
        action: Action,
        user_id: int,
        *,
        dice_value: int | None = None,
        page: int | None = None,
        target_user_id: int | None = None,
        title_id: int | None = None,
        anime_genre: AnimeGenre | None = None,
    ) -> str:
        return json.dumps(
            {
                field: value
                for field, value in {
                    Field.ACTION_TYPE.value: action.value,
                    Field.USER_ID.value: user_id,
                    Field.DICE_VALUE.value: dice_value,
                    Field.PAGE.value: page,
                    Field.TARGET_USER_ID.value: target_user_id,
                    Field.TITLE_BAG_ID.value: title_id,
                    Field.ANIME_GENRE.value: anime_genre.value if anime_genre else None,
                }.items()
                if value is not None
            }
        )

    @staticmethod
    def dump_empty():
        return json.dumps({})

    @staticmethod
    def load(data: str | None) -> Payload | None:
        if data is None:
            return None
        parsed = parse_json(data)
        action = Action(parsed.get(Field.ACTION_TYPE.value))
        user_id = PayloadFactory._extract_field(parsed, Field.USER_ID)
        if not action or not user_id:
            return None
        anime_genre = PayloadFactory._extract_field(parsed, Field.ANIME_GENRE)
        return Payload(
            action=action,
            user_id=user_id,
            genre=AnimeGenre(anime_genre) if anime_genre else None,
            dice_value=PayloadFactory._extract_field(parsed, Field.DICE_VALUE),
            page=PayloadFactory._extract_field(parsed, Field.PAGE),
            target_id=PayloadFactory._extract_field(parsed, Field.TARGET_USER_ID),
            title_bag_id=PayloadFactory._extract_field(parsed, Field.TITLE_BAG_ID),
        )

    @staticmethod
    def has_action(data: str | None, actions: set[Action]) -> bool:
        if payload := PayloadFactory.load(data):
            return payload.action in actions
        return False

    @staticmethod
    def _extract_field(parsed: dict, field: Field) -> int | None:
        value = str(parsed.get(field.value, "")).lstrip("-")
        return int(value) if value.isdigit() else None

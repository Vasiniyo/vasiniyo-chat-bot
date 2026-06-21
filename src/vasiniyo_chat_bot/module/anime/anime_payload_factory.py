from dataclasses import dataclass
import json

from vasiniyo_chat_bot.module.anime.dto import AnimeGenre
from vasiniyo_chat_bot.module.dto import Action
from vasiniyo_chat_bot.module.dto import Field
from vasiniyo_chat_bot.safely_bot_utils import extract_field
from vasiniyo_chat_bot.safely_bot_utils import parse_json


@dataclass(frozen=True)
class AnimePayload:
    action: Action
    user_id: int
    genre: AnimeGenre


class AnimePayloadFactory:
    _valid_payload_actions = {Action.ANIME.value}

    @staticmethod
    def has_anime_payload(data: str) -> bool:
        payload = parse_json(data)
        return (
            payload.get(Field.ACTION_TYPE.value)
            in AnimePayloadFactory._valid_payload_actions
        )

    @staticmethod
    def get_payload(data: str) -> AnimePayload:
        payload = parse_json(data)
        action_value = payload.get(Field.ACTION_TYPE.value)
        action = Action._value2member_map_.get(action_value)
        return AnimePayload(
            action=action if isinstance(action, Action) else None,
            user_id=extract_field(payload, Field.USER_ID),
            genre=AnimeGenre(extract_field(payload, Field.ANIME_GENRE)),
        )

    @staticmethod
    def anime_genre(user_id: int, genre: AnimeGenre) -> str:
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.ANIME.value,
                Field.USER_ID.value: user_id,
                Field.ANIME_GENRE.value: genre.value,
            }
        )

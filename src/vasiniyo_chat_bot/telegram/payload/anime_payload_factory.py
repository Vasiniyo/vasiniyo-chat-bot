import json

from vasiniyo_chat_bot.module.anime.dto import AnimeGenre
from vasiniyo_chat_bot.safely_bot_utils import parse_json
from vasiniyo_chat_bot.telegram.dto import Action, Field


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
    def anime_genre(user_id: int, genre: AnimeGenre) -> str:
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.ANIME.value,
                Field.USER_ID.value: user_id,
                Field.ANIME_GENRE.value: genre.value,
            }
        )

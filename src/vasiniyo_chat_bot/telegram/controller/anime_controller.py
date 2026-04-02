from telebot.types import CallbackQuery, Message

from vasiniyo_chat_bot.module.anime.anime_service import AnimeService
from vasiniyo_chat_bot.module.anime.dto import AnimeGenre
from vasiniyo_chat_bot.safely_bot_utils import extract_field, parse_json
from vasiniyo_chat_bot.telegram.bot_service import BotService
from vasiniyo_chat_bot.telegram.dto import Action, Field
from vasiniyo_chat_bot.telegram.renderer.anime_renderer import AnimeRenderer


class AnimeController:
    def __init__(
        self,
        bot_service: BotService,
        anime_service: AnimeService,
        anime_renderer: AnimeRenderer,
    ) -> None:
        self._bot_service = bot_service
        self.anime_service = anime_service
        self.anime_renderer = anime_renderer

    def handle_anime_command(self, message: Message):
        self.anime_renderer.send_genres_buttons(
            message.chat.id, message.id, message.from_user.id
        )

    def dispatch_anime_callback(self, call: CallbackQuery):
        payload = parse_json(call.data)
        payload_user_id = extract_field(payload, Field.USER_ID)
        anime_genre = extract_field(payload, Field.ANIME_GENRE)
        message = call.message
        user_id = call.from_user.id
        if user_id != payload_user_id:
            self._bot_service.answer_callback_query(
                "Эти кнопки были не для тебя!", call.id
            )
            return
        anime = self.anime_service.handle_anime(
            score=8, anime_genre=AnimeGenre(anime_genre)
        )
        self.anime_renderer.send_anime(anime, message.chat.id, message.id)

    @staticmethod
    def has_anime_payload(call: CallbackQuery) -> bool:
        return parse_json(call.data).get(Field.ACTION_TYPE.value) == Action.ANIME.value

import json

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from vasiniyo_chat_bot.module.anime.dto import Anime, AnimeGenre
from vasiniyo_chat_bot.telegram.bot_service import BotService
from vasiniyo_chat_bot.telegram.dto import Action, Field


class AnimeRenderer:
    _genres = {
        AnimeGenre.ADVENTURE: "Приключения",
        AnimeGenre.ACTION: "Экшен",
        AnimeGenre.COMEDY: "Комедия",
        AnimeGenre.DRAMA: "Драма",
        AnimeGenre.FANTASY: "Фэнтези",
        AnimeGenre.HORROR: "Хоррор",
        AnimeGenre.MYSTERY: "Мистика",
        AnimeGenre.ROMANCE: "Романтика",
        AnimeGenre.SCI_FI: "Научная фантастика",
        AnimeGenre.SLICE: "Повседневность",
        AnimeGenre.SPORTS: "Спорт",
        AnimeGenre.THRILLER: "Триллер",
        AnimeGenre.RANDOM: "Случайное",
    }
    _groups = [
        [AnimeGenre.ADVENTURE, AnimeGenre.ACTION, AnimeGenre.COMEDY],
        [AnimeGenre.DRAMA, AnimeGenre.FANTASY, AnimeGenre.HORROR],
        [AnimeGenre.MYSTERY, AnimeGenre.ROMANCE, AnimeGenre.SCI_FI],
        [AnimeGenre.SLICE, AnimeGenre.SPORTS, AnimeGenre.THRILLER],
        [AnimeGenre.RANDOM],
    ]

    def __init__(self, bot_service: BotService):
        self.bot_service = bot_service

    def send_anime(self, anime: Anime, chat_id: int, message_id: int):
        if not anime.link:
            self.bot_service.edit_message_text(
                "Я не могу вспомнить ни одно аниме...", chat_id, message_id
            )
        else:
            self.bot_service.edit_message_text(
                anime.link, chat_id, message_id, is_disabled_preview=False
            )

    def send_genres_buttons(self, chat_id: int, message_id: int, user_id: int):
        markup = InlineKeyboardMarkup()
        for group in self._groups:
            markup.add(
                *[
                    InlineKeyboardButton(
                        self._genres.get(genre),
                        callback_data=self._create_anime_genre_payload(user_id, genre),
                    )
                    for genre in group
                ]
            )
        self.bot_service.send_message(
            "Выберите жанр аниме:", chat_id, message_id, reply_markup=markup
        )

    @staticmethod
    def _create_anime_genre_payload(user_id: int, anime_genre: AnimeGenre) -> str:
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.ANIME.value,
                Field.USER_ID.value: user_id,
                Field.ANIME_GENRE.value: anime_genre.value,
            }
        )

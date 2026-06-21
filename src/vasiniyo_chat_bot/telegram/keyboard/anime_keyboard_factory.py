from telebot.types import InlineKeyboardButton
from telebot.types import InlineKeyboardMarkup

from vasiniyo_chat_bot.module.anime.anime_payload_factory import AnimePayloadFactory
from vasiniyo_chat_bot.module.anime.dto import AnimeGenre


class AnimeKeyboardFactory:
    def __init__(self, payload_factory: AnimePayloadFactory):
        self._payload_factory = payload_factory

    _groups = [
        [AnimeGenre.ADVENTURE, AnimeGenre.ACTION, AnimeGenre.COMEDY],
        [AnimeGenre.DRAMA, AnimeGenre.FANTASY, AnimeGenre.HORROR],
        [AnimeGenre.MYSTERY, AnimeGenre.ROMANCE, AnimeGenre.SCI_FI],
        [AnimeGenre.SLICE, AnimeGenre.SPORTS, AnimeGenre.THRILLER],
        [AnimeGenre.RANDOM],
    ]
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

    def genre_options_markup(self, user_id: int) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        for group in self._groups:
            markup.add(*[self._anime_genre(user_id, genre) for genre in group])
        return markup

    def _anime_genre(self, user_id: int, genre: AnimeGenre) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            self._genres.get(genre),
            callback_data=self._payload_factory.anime_genre(user_id, genre),
        )

from telebot.types import InlineKeyboardButton
from telebot.types import InlineKeyboardMarkup

from vasiniyo_chat_bot.module.dto import Action
from vasiniyo_chat_bot.module.dto import AnimeGenre
from vasiniyo_chat_bot.module.payload_factory import PayloadFactory


class AnimeKeyboardFactory:
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

    @staticmethod
    def anime_menu(user_id: int) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        for group in AnimeKeyboardFactory._groups:
            markup.add(
                *[AnimeKeyboardFactory._anime_genre(user_id, genre) for genre in group]
            )
        return markup

    @staticmethod
    def _anime_genre(user_id: int, genre: AnimeGenre) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            AnimeKeyboardFactory._genres.get(genre, genre.name),
            callback_data=PayloadFactory.dump(Action.ANIME, user_id, anime_genre=genre),
        )

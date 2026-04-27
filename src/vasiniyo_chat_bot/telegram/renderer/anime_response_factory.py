from vasiniyo_chat_bot.module.anime.dto import Anime
from vasiniyo_chat_bot.telegram.dto import Response
from vasiniyo_chat_bot.telegram.keyboard.anime_keyboard_factory import (
    AnimeKeyboardFactory,
)


class AnimeResponseFactory:
    def __init__(self, keyboard_factory: AnimeKeyboardFactory):
        self._keyboard_factory = keyboard_factory

    @staticmethod
    def link(anime: Anime):
        text = anime.link or "Я не могу вспомнить ни одно аниме..."
        return Response(text_units=text)

    def genre_options(self, user_id: int):
        text = "Выберите жанр аниме:"
        markup = self._keyboard_factory.genre_options_markup(user_id)
        return Response(text_units=text, markup=markup)

    @staticmethod
    def no_access():
        text = "Эти кнопки были не для тебя!"
        return Response(text_units=text)

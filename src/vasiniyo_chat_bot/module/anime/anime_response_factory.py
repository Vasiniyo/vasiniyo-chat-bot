from vasiniyo_chat_bot.module.anime.dto import Anime
from vasiniyo_chat_bot.module.dto import Response
from vasiniyo_chat_bot.module.titles.dto import AnimeGenreMenu


class AnimeResponseFactory:
    @staticmethod
    def link(anime: Anime):
        text = anime.link or "Я не могу вспомнить ни одно аниме..."
        return Response(text_units=text)

    @staticmethod
    def genre_options():
        text = "Выберите жанр аниме:"
        return Response(text_units=text, menu=AnimeGenreMenu())

    @staticmethod
    def no_access():
        text = "Эти кнопки были не для тебя!"
        return Response(text_units=text)

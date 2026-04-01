from telebot.types import Message

from vasiniyo_chat_bot.module.anime.anime_service import AnimeService
from vasiniyo_chat_bot.telegram.renderer.anime_renderer import AnimeRenderer


class AnimeController:
    def __init__(
        self, anime_service: AnimeService, anime_renderer: AnimeRenderer
    ) -> None:
        self.anime_service = anime_service
        self.anime_renderer = anime_renderer

    def handle_anime_command(self, message: Message):
        anime = self.anime_service.handle_anime(score=8)
        self.anime_renderer.send_anime(anime, message.chat.id, message.id)

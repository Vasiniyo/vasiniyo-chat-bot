from vasiniyo_chat_bot.module.anime.dto import Anime
from vasiniyo_chat_bot.telegram.bot_service import BotService


class AnimeRenderer:
    def __init__(self, bot_service: BotService):
        self.bot_service = bot_service

    def send_anime(self, anime: Anime, chat_id: int, message_id: int):
        if not anime.link:
            self.bot_service.send_message(
                "Я не могу вспомнить ни одно аниме...", chat_id, message_id
            )
        else:
            self.bot_service.send_message(
                anime.link, chat_id, message_id, is_disabled_preview=False
            )

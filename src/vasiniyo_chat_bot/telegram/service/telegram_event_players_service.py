from telebot.types import ChatMemberAdministrator, ChatMemberOwner

from vasiniyo_chat_bot.module.play.event_player_service import EventPlayersService
from vasiniyo_chat_bot.telegram.bot_service import BotService


class TelegramEventPlayersService(EventPlayersService):
    def __init__(self, bot_service: BotService):
        self._bot_service = bot_service

    def get_players(self, chat_id: int) -> list[int]:
        return [
            admin.user.id
            for admin in self._bot_service.get_chat_administrators(chat_id)
            if not admin.user.is_bot
            and isinstance(admin, ChatMemberAdministrator)
            or isinstance(admin, ChatMemberOwner)
        ]

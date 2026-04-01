from vasiniyo_chat_bot.telegram.bot_service import BotService


class EventPlayersRepository:
    def __init__(self, bot_service: BotService):
        self.bot_service = bot_service

    def get_players(self, chat_id: int) -> list[int]:
        return [
            admin.user.id
            for admin in self.bot_service.get_chat_administrators(chat_id)
            if admin.can_be_edited or admin.status == "creator"
        ]

from vasiniyo_chat_bot.module.likes.dto import Leaderboard, Like
from vasiniyo_chat_bot.telegram.bot_service import BotService, UserTemplate


class LikeRenderer:
    def __init__(self, bot_service: BotService):
        self.bot_service = bot_service

    def send_like(self, like: Like, chat_id: int, message_id: int, user_id: int):
        if not like.current_likes:
            self.bot_service.send_message(
                "🤯 Я не понимаю кому ставить лайк, отправь его ответом на сообщение что ли...",
                chat_id,
                message_id,
            )
        else:
            self.bot_service.send_message(
                [
                    f"👍 Лайк засчитан!\nУ ",
                    UserTemplate(chat_id, user_id),
                    f" теперь {like.current_likes} лайков!",
                ],
                chat_id,
                message_id,
            )

    def send_leaderboard(self, leaderboard: Leaderboard, chat_id: int, message_id: int):
        self.bot_service.send_leaderboard(
            leaderboard, "🏆 Топ по лайкам:", chat_id, message_id
        )

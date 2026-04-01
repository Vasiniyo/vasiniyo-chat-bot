from telebot.types import Message

from vasiniyo_chat_bot.module.likes.like_service import LikeService
from vasiniyo_chat_bot.telegram.renderer.like_renderer import LikeRenderer


class LikeController:
    def __init__(self, like_service: LikeService, like_renderer: LikeRenderer) -> None:
        self.like_service = like_service
        self.like_renderer = like_renderer

    def set_like(self, message: Message):
        chat_id = message.chat.id
        from_user_id = message.from_user.id
        to_user_id = (
            message.reply_to_message.from_user.id if message.reply_to_message else None
        )
        like = self.like_service.handle_like(chat_id, from_user_id, to_user_id)
        self.like_renderer.send_like(like, chat_id, message.id, to_user_id)

    def top_likes(self, message: Message):
        chat_id = message.chat.id
        leaderboard = self.like_service.handle_top_likes(chat_id)
        self.like_renderer.send_leaderboard(leaderboard, chat_id, message.id)

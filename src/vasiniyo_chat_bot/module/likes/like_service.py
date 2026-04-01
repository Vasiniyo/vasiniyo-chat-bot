from vasiniyo_chat_bot.database.sqlite.repository.sqlite_likes_repository import (
    SqliteLikesRepository,
)
from vasiniyo_chat_bot.module.likes.dto import Leaderboard, Like


class LikeService:
    def __init__(self, likes_repository: SqliteLikesRepository):
        self.likes_repository = likes_repository

    def handle_top_likes(self, chat_id: int) -> Leaderboard:
        return self.likes_repository.get_leaderboard(chat_id, 10)

    def handle_like(self, chat_id: int, from_user_id: int, to_user_id: int) -> Like:
        if not to_user_id:
            return Like(current_likes=None)
        current_likes = self.likes_repository.like_and_count(
            chat_id, from_user_id, to_user_id
        )
        return Like(current_likes=current_likes)

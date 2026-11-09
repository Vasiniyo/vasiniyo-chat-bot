from injector import inject

from vasiniyo_chat_bot.database.database import Database
from vasiniyo_chat_bot.database.entity import LikeEntity
from vasiniyo_chat_bot.database.repository.likes_repository import LikesRepository
from vasiniyo_chat_bot.module.dto import Leaderboard
from vasiniyo_chat_bot.module.dto import LeaderboardRow
from vasiniyo_chat_bot.module.like.dto import Like


@inject
class LikeService:
    def __init__(self, likes_repository: LikesRepository, database: Database):
        self._likes_repository = likes_repository
        self._database = database

    def handle_top_likes(self, chat_id: int) -> Leaderboard:
        with self._database.session() as session:
            with session.begin():
                return Leaderboard(
                    chat_id=chat_id,
                    rows=[
                        LeaderboardRow(user_id=row.user_id, value=row.like_count)
                        for row in self._likes_repository.get_leaderboard(
                            session, chat_id, 10
                        )
                    ],
                )

    def handle_like(self, chat_id: int, from_user_id: int, to_user_id: int) -> Like:
        with self._database.session() as session:
            with session.begin():
                self._likes_repository.set_like(
                    session,
                    LikeEntity(
                        chat_id=chat_id,
                        from_user_id=from_user_id,
                        to_user_id=to_user_id,
                    ),
                )
                current_likes = self._likes_repository.count_by_chat_and_to_user(
                    session, chat_id, to_user_id
                )
                return Like(current_likes=current_likes)

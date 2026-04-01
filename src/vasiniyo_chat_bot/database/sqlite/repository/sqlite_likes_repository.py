from __future__ import annotations

from sqlite3 import Connection

from vasiniyo_chat_bot.database.sqlite.dao.likes_dao import LikesDao
from vasiniyo_chat_bot.database.sqlite.repository.dto import SqliteDatabaseSettings
from vasiniyo_chat_bot.database.sqlite.repository.sqlite_repository import (
    SqliteRepository,
)
from vasiniyo_chat_bot.module.likes.dto import Leaderboard, LeaderboardRow
from vasiniyo_chat_bot.module.likes.likes_repository import LikesRepository


class SqliteLikesRepository(SqliteRepository, LikesRepository):
    def __init__(self, likesDao: LikesDao, settings: SqliteDatabaseSettings):
        super().__init__(settings)
        self.likesDao = likesDao

    def like_and_count(self, chat_id: int, from_user_id: int, to_user_id: int) -> int:
        def _tx(conn: Connection):
            self.likesDao.save(conn, chat_id, from_user_id, to_user_id)
            return self.likesDao.count_by_chat_and_to_user(conn, chat_id, to_user_id)

        return self.transaction(_tx)

    def get_leaderboard(self, chat_id: int, limit: int) -> Leaderboard:
        def _tx(conn: Connection):
            return Leaderboard(
                chat_id=chat_id,
                rows=[
                    LeaderboardRow(user_id=row[0], value=row[1])
                    for row in self.likesDao.get_leaderboard(conn, chat_id, limit)
                ],
            )

        return self.transaction(_tx)

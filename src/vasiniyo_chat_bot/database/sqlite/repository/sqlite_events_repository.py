from __future__ import annotations

from sqlite3 import Connection

from vasiniyo_chat_bot.database.sqlite.dao.events_dao import EventsDao
from vasiniyo_chat_bot.database.sqlite.repository.dto import SqliteDatabaseSettings
from vasiniyo_chat_bot.database.sqlite.repository.sqlite_repository import (
    SqliteRepository,
)
from vasiniyo_chat_bot.module.likes.dto import Leaderboard, LeaderboardRow
from vasiniyo_chat_bot.module.play.events_repository import EventsRepository


class SqliteEventsRepository(SqliteRepository, EventsRepository):
    def __init__(self, eventsDao: EventsDao, settings: SqliteDatabaseSettings):
        super().__init__(settings)
        self.eventsDao = eventsDao

    def insert_winner(self, chat_id: int, user_id: int, event_id: int) -> int:
        return self.transaction(
            lambda conn: self.eventsDao.save(conn, chat_id, user_id, event_id)
        ).winner_user_id

    def get_last_winner(self, chat_id: int, event_id: int) -> int | None:
        return self.transaction(
            lambda conn: self.eventsDao.get_last_winner(conn, chat_id, event_id)
        )

    def is_day_passed(self, chat_id: int, event_id: int) -> bool:
        return self.transaction(
            lambda conn: self.eventsDao.is_day_passed(conn, chat_id, event_id)
        )

    def get_leaderboard(self, chat_id: int, event_id: int, limit: int) -> Leaderboard:
        def _tx(conn: Connection) -> list[tuple[int, int]]:
            return self.eventsDao.fetch_top(conn, chat_id, event_id, limit)

        return Leaderboard(
            chat_id=chat_id,
            rows=[
                LeaderboardRow(user_id=row[0], value=row[1])
                for row in self.transaction(_tx)
            ],
        )

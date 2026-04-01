from sqlite3 import Connection

from vasiniyo_chat_bot.database.sqlite.entity import EventEntity
from vasiniyo_chat_bot.database.sqlite.util import SQLiteDao


class EventsDao:
    @staticmethod
    def save(
        conn: Connection, chat_id: int, user_id: int, event_id: int
    ) -> EventEntity:
        result_row = SQLiteDao.fetchone(
            conn,
            """
            insert into events (chat_id, winner_user_id, event_id, last_played)
            values (?, ?, ?, strftime('%s', 'now'))
            on conflict do nothing
            returning chat_id, winner_user_id, event_id, last_played
            """,
            (chat_id, user_id, event_id),
        )
        return EventEntity(
            chat_id=result_row[0],
            winner_user_id=result_row[1],
            event_id=result_row[2],
            last_played=result_row[3],
        )

    @staticmethod
    def get_last_winner(conn: Connection, chat_id: int, event_id: int) -> int | None:
        result_row = SQLiteDao.fetchone(
            conn,
            """
           select winner_user_id
           from events
           where chat_id = ?
           and event_id = ?
           order by last_played desc
           limit 1
           """,
            (chat_id, event_id),
        )
        return result_row[0] if result_row else None

    @staticmethod
    def fetch_top(
        conn: Connection, chat_id: int, event_id: int, limit: int
    ) -> list[tuple[int, int]]:
        return SQLiteDao.fetchall(
            conn,
            """
            select winner_user_id, winner_count
            from (select distinct winner_user_id,
                                  count(*) over (partition by winner_user_id) as winner_count
                  from events
                  where chat_id = ?
                  and event_id = ?)
            order by winner_count desc
            limit ?            
            """,
            (chat_id, event_id, limit),
        )

    @staticmethod
    def is_day_passed(conn: Connection, chat_id: int, event_id: int) -> bool:
        result_row = SQLiteDao.fetchone(
            conn,
            """
           select date('now', 'localtime') > date(max(last_played), 'unixepoch', 'localtime')
           from events
           where chat_id = ?
           and event_id = ?
           group by chat_id, event_id
           """,
            (chat_id, event_id),
        )
        return bool(result_row[0]) if result_row else None

    @staticmethod
    def remove(
        conn: Connection, chat_id: int, user_id: int, event_id: int, last_played: int
    ):
        SQLiteDao.fetchone(
            conn,
            """
            delete from events
            where chat_id = ?
            and winner_user_id = ?
            and event_id = ?
            and last_played = ?
            """,
            (chat_id, user_id, event_id, last_played),
        )

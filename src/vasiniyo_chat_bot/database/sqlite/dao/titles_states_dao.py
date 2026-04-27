from sqlite3 import Connection

from vasiniyo_chat_bot.database.sqlite.entity.title_entity import TitlesStateEntity
from vasiniyo_chat_bot.database.sqlite.util import SQLiteDao


class TitlesStatesDAO:
    @staticmethod
    def save(conn: Connection, chat_id: int, user_id: int) -> TitlesStateEntity:
        result_row = SQLiteDao.fetchone(
            conn,
            """
            insert into titles_states (chat_id, user_id, last_changing)
            values (?, ?, 0)
            on conflict (chat_id, user_id) do update set 
            last_changing = excluded.last_changing
            returning chat_id, user_id, last_changing
            """,
            (chat_id, user_id),
        )
        return TitlesStateEntity(
            chat_id=result_row[0], user_id=result_row[1], last_changing=result_row[2]
        )

    @staticmethod
    def update_last_changing(conn: Connection, chat_id: int, user_id: int):
        SQLiteDao.execute(
            conn,
            """
            update titles_states
            set last_changing = strftime('%s', 'now')
            where chat_id = ?
            and user_id = ?
            """,
            (chat_id, user_id),
        )

    @staticmethod
    def is_day_passed(conn: Connection, chat_id: int, user_id: int) -> bool:
        result_row = SQLiteDao.fetchone(
            conn,
            """
            select date('now', 'localtime') > date(last_changing, 'unixepoch', 'localtime')
            from titles_states
            where chat_id = ?
            and user_id = ?
            """,
            (chat_id, user_id),
        )
        return bool(result_row[0]) if result_row else None

    @staticmethod
    def remove(conn: Connection, chat_id: int, user_id: int):
        SQLiteDao.fetchone(
            conn,
            """
            delete from titles_states
            where chat_id = ?
            and user_id = ?
            """,
            (chat_id, user_id),
        )

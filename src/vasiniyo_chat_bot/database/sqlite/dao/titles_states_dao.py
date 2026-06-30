from sqlite3 import Connection

from vasiniyo_chat_bot.database.sqlite.entity.title_entity import TitlesStateEntity
from vasiniyo_chat_bot.database.sqlite.util import SQLiteDao


class TitlesStatesDAO:
    @staticmethod
    def save(conn: Connection, chat_id: int, user_id: int) -> TitlesStateEntity:
        result_row = SQLiteDao.fetchone(
            conn,
            """
            insert into titles_states (chat_id, user_id, last_changing, extra_rolls)
            values (?, ?, 0, 0)
            on conflict (chat_id, user_id) do update set 
            last_changing = excluded.last_changing,
            extra_rolls = excluded.extra_rolls
            returning chat_id, user_id, last_changing, extra_rolls
            """,
            (chat_id, user_id),
        )
        return TitlesStateEntity(
            chat_id=result_row[0],
            user_id=result_row[1],
            last_changing=result_row[2],
            extra_rolls=result_row[3],
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
            returning extra_rolls
            """,
            (chat_id, user_id),
        )

    @staticmethod
    def increase_extra_rolls(conn: Connection, chat_id: int, user_id: int) -> int:
        result_row = SQLiteDao.fetchone(
            conn,
            """
            update titles_states
            set extra_rolls = extra_rolls + 1
            where chat_id = ?
            and user_id = ?
            returning extra_rolls
            """,
            (chat_id, user_id),
        )
        return result_row[0] if result_row else 0

    @staticmethod
    def decrease_extra_rolls(conn: Connection, chat_id: int, user_id: int) -> int:
        result_row = SQLiteDao.fetchone(
            conn,
            """
            update titles_states
            set extra_rolls = max(0, extra_rolls - 1)
            where chat_id = ?
            and user_id = ?
            returning extra_rolls
            """,
            (chat_id, user_id),
        )
        return result_row[0] if result_row else 0

    @staticmethod
    def get_extra_rolls(conn: Connection, chat_id: int, user_id: int) -> int:
        result_row = SQLiteDao.fetchone(
            conn,
            """
            select extra_rolls
            from titles_states
            where chat_id = ?
            and user_id = ?
            """,
            (chat_id, user_id),
        )
        return result_row[0] if result_row else 0

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

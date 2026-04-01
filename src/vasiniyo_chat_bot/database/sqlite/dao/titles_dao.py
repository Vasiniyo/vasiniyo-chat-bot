from sqlite3 import Connection

from vasiniyo_chat_bot.database.sqlite.entity.title_entity import TitleEntity
from vasiniyo_chat_bot.database.sqlite.util import SQLiteDao


class TitlesDAO:
    @staticmethod
    def save(
        conn: Connection, chat_id: int, user_id: int, user_title: str
    ) -> TitleEntity:
        result_row = SQLiteDao.fetchone(
            conn,
            """
            insert into titles (chat_id, user_id, user_title, last_changing)
            values (?, ?, ?, 0)
            on conflict (chat_id, user_id) do update set 
            user_title = excluded.user_title,
            last_changing = excluded.last_changing
            returning chat_id, user_id, user_title, last_changing
            """,
            (chat_id, user_id, user_title),
        )
        return TitleEntity(
            chat_id=result_row[0],
            user_id=result_row[1],
            user_title=result_row[2],
            last_changing=result_row[3],
        )

    @staticmethod
    def update_user_title_and_last_changing(
        conn: Connection, chat_id: int, user_id: int, user_title: str
    ):
        SQLiteDao.execute(
            conn,
            """
            update titles
            set user_title = ?,
                last_changing = strftime('%s', 'now')
            where chat_id = ?
            and user_id = ?
            """,
            (user_title, chat_id, user_id),
        )

    @staticmethod
    def update_user_title(
        conn: Connection, chat_id: int, user_id: int, user_title: str
    ):
        SQLiteDao.execute(
            conn,
            """
            update titles
            set user_title = ?
            where chat_id = ?
            and user_id = ?
            """,
            (user_title, chat_id, user_id),
        )

    @staticmethod
    def update_last_changing(conn: Connection, chat_id: int, user_id: int):
        SQLiteDao.execute(
            conn,
            """
            update titles
            set last_changing = strftime('%s', 'now')
            where chat_id = ?
            and user_id = ?
            """,
            (chat_id, user_id),
        )

    @staticmethod
    def find_title(conn: Connection, chat_id: int, user_id: int) -> str | None:
        result_row = SQLiteDao.fetchone(
            conn,
            """
            select user_title
            from titles
            where chat_id = ?
            and user_id = ?
            """,
            (chat_id, user_id),
        )
        return result_row[0] if result_row else None

    @staticmethod
    def get_titles_by_chat(conn: Connection, chat_id: int) -> list[TitleEntity]:
        result_set = SQLiteDao.fetchall(
            conn,
            """
            select chat_id, user_id, user_title, last_changing
            from titles
            where chat_id = ?
            """,
            (chat_id,),
        )
        return [
            TitleEntity(
                chat_id=row[0], user_id=row[1], user_title=row[2], last_changing=row[3]
            )
            for row in result_set
        ]

    @staticmethod
    def is_day_passed(conn: Connection, chat_id: int, user_id: int) -> bool:
        result_row = SQLiteDao.fetchone(
            conn,
            """
            select date('now', 'localtime') > date(last_changing, 'unixepoch', 'localtime')
            from titles
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
            delete from titles
            where chat_id = ?
            and user_id = ?
            """,
            (chat_id, user_id),
        )

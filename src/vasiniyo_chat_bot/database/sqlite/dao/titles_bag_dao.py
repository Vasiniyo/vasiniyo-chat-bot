from sqlite3 import Connection

from vasiniyo_chat_bot.database.sqlite.entity.title_bag_entity import TitlesBagEntity
from vasiniyo_chat_bot.database.sqlite.util import SQLiteDao


class TitlesBagDAO:
    @staticmethod
    def save(
        conn: Connection, chat_id: int, user_id: int, user_title: str
    ) -> TitlesBagEntity:
        result_row = SQLiteDao.fetchone(
            conn,
            """
            insert into titles_bag (chat_id, user_id, user_title)
            values (?, ?, ?)
            returning chat_id, user_id, user_title, id
            """,
            (chat_id, user_id, user_title),
        )
        return TitlesBagEntity(
            chat_id=result_row[0],
            user_id=result_row[1],
            user_title=result_row[2],
            id=result_row[3],
        )

    @staticmethod
    def get_by_chat_and_user(
        conn: Connection, chat_id: int, user_id: int
    ) -> list[TitlesBagEntity]:
        result_set = SQLiteDao.fetchall(
            conn,
            """
            select id, chat_id, user_id, user_title
            from titles_bag
            where chat_id = ?
            and user_id = ?
            """,
            (chat_id, user_id),
        )
        return [
            TitlesBagEntity(
                id=row[0], chat_id=row[1], user_id=row[2], user_title=row[3]
            )
            for row in result_set
        ]

    @staticmethod
    def find_by_id(conn: Connection, titles_bag_id: int) -> TitlesBagEntity | None:
        row = SQLiteDao.fetchone(
            conn,
            """
            select id, chat_id, user_id, user_title
            from titles_bag
            where id = ?
            """,
            (titles_bag_id,),
        )
        if not row:
            return None
        return TitlesBagEntity(
            id=row[0], chat_id=row[1], user_id=row[2], user_title=row[3]
        )

    @staticmethod
    def remove_by_id(conn: Connection, titles_bag_id: int) -> None:
        SQLiteDao.execute(
            conn,
            """
            delete from titles_bag
            where id = ?
            """,
            (titles_bag_id,),
        )

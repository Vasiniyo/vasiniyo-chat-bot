from sqlite3 import Connection

from vasiniyo_chat_bot.database.sqlite.entity.title_bag_entity import TitlesBagEntity
from vasiniyo_chat_bot.database.sqlite.util import SQLiteDao


class TitlesBagDAO:
    @staticmethod
    def save(conn: Connection, entity: TitlesBagEntity) -> TitlesBagEntity:
        result_row = SQLiteDao.fetchone(
            conn,
            """
            insert into titles_bag (id, chat_id, user_id, user_title, is_inventory)
            values (?, ?, ?, ?, ?)
            on conflict (id)
            do update set
                chat_id=excluded.chat_id,
                user_id=excluded.user_id,
                user_title = excluded.user_title,
                is_inventory = excluded.is_inventory
            returning id, chat_id, user_id, user_title, is_inventory
            """,
            (
                entity.id,
                entity.chat_id,
                entity.user_id,
                entity.user_title,
                entity.is_inventory,
            ),
        )
        return TitlesBagEntity(
            id=result_row[0],
            chat_id=result_row[1],
            user_id=result_row[2],
            user_title=result_row[3],
            is_inventory=result_row[4],
        )

    @staticmethod
    def get_by_chat_and_user(
        conn: Connection, chat_id: int, user_id: int, is_inventory: bool
    ) -> list[TitlesBagEntity]:
        result_set = SQLiteDao.fetchall(
            conn,
            """
            select id, chat_id, user_id, user_title, is_inventory
            from titles_bag
            where chat_id = ?
            and user_id = ?
            and is_inventory = ?
            """,
            (chat_id, user_id, is_inventory),
        )
        return [
            TitlesBagEntity(
                id=row[0],
                chat_id=row[1],
                user_id=row[2],
                user_title=row[3],
                is_inventory=row[4],
            )
            for row in result_set
        ]

    @staticmethod
    def get_by_chat(conn: Connection, chat_id: int) -> list[TitlesBagEntity]:
        result_set = SQLiteDao.fetchall(
            conn,
            """
            select id, chat_id, user_id, user_title, is_inventory
            from titles_bag
            where chat_id = ?
            """,
            (chat_id,),
        )
        return [
            TitlesBagEntity(
                id=row[0],
                chat_id=row[1],
                user_id=row[2],
                user_title=row[3],
                is_inventory=row[4],
            )
            for row in result_set
        ]

    @staticmethod
    def find_by_id(conn: Connection, titles_bag_id: int) -> TitlesBagEntity | None:
        row = SQLiteDao.fetchone(
            conn,
            """
            select id, chat_id, user_id, user_title, is_inventory
            from titles_bag
            where id = ?
            """,
            (titles_bag_id,),
        )
        if not row:
            return None
        return TitlesBagEntity(
            id=row[0],
            chat_id=row[1],
            user_id=row[2],
            user_title=row[3],
            is_inventory=row[4],
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

    @staticmethod
    def find_current(conn, chat_id, user_id) -> TitlesBagEntity | None:
        row = SQLiteDao.fetchone(
            conn,
            """
            select id, chat_id, user_id, user_title, is_inventory
            from titles_bag
            where chat_id = ?
            and user_id = ?
            and not is_inventory
            """,
            (chat_id, user_id),
        )
        return (
            None
            if not row
            else TitlesBagEntity(
                id=row[0],
                chat_id=row[1],
                user_id=row[2],
                user_title=row[3],
                is_inventory=row[4],
            )
        )

    @staticmethod
    def get_titles_by_chat(conn, chat_id) -> list[TitlesBagEntity]:
        result_set = SQLiteDao.fetchall(
            conn,
            """
            select id, chat_id, user_id, user_title, is_inventory
            from titles_bag
            where chat_id = ?
            """,
            (chat_id,),
        )
        return [
            TitlesBagEntity(
                id=row[0],
                chat_id=row[1],
                user_id=row[2],
                user_title=row[3],
                is_inventory=row[4],
            )
            for row in result_set
        ]

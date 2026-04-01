from sqlite3 import Connection

from vasiniyo_chat_bot.database.sqlite.entity.like_entity import LikeEntity
from vasiniyo_chat_bot.database.sqlite.util import SQLiteDao


class LikesDao:
    @staticmethod
    def save(
        conn: Connection, chat_id: int, from_user_id: int, to_user_id: int
    ) -> LikeEntity:
        result_row = SQLiteDao.fetchone(
            conn,
            """
            insert into likes (chat_id, from_user_id, to_user_id)
            values (?, ?, ?)
            on conflict (chat_id, from_user_id) do update set to_user_id = ?
            returning chat_id, from_user_id, to_user_id
            """,
            (chat_id, from_user_id, to_user_id, to_user_id),
        )
        return LikeEntity(
            chat_id=result_row[0], from_user_id=result_row[1], to_user_id=result_row[2]
        )

    @staticmethod
    def get_leaderboard(
        conn: Connection, chat_id: int, limit: int
    ) -> list[tuple[int, int]]:
        return SQLiteDao.fetchall(
            conn,
            """
            select to_user_id, like_count
            from (select distinct to_user_id,
                                  count(*) over (partition by to_user_id) as like_count
                  from likes
                  where chat_id = ?)
            order by like_count desc
            limit ?            
            """,
            (chat_id, limit),
        )

    @staticmethod
    def count_by_chat_and_to_user(
        conn: Connection, chat_id: int, to_user_id: int
    ) -> int:
        result_row = SQLiteDao.fetchone(
            conn,
            """
            select count(to_user_id)
            from likes 
            where chat_id = ? 
            and to_user_id = ?
            """,
            (chat_id, to_user_id),
        )
        return result_row[0] if result_row else None

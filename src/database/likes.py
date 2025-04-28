import sqlite3

from database.utils import commit_query, database_name, fetch_number


def count_likes(chat_id, to_user_id):
    return fetch_number(
        """
        select count(to_user_id) 
        from likes 
        where chat_id = ? 
        and to_user_id = ?
        """,
        (chat_id, to_user_id),
    )


def fetch_top(chat_id, limit):
    with sqlite3.connect(database_name) as connection:
        return connection.execute(
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
        ).fetchall()


def add_like(chat_id, from_user_id, to_user_id):
    commit_query(
        """
        insert into likes (chat_id, from_user_id, to_user_id) values (?, ?, ?)
        on conflict (chat_id, from_user_id) do update set to_user_id = ?
        """,
        (chat_id, from_user_id, to_user_id, to_user_id),
    )


commit_query(
    """
    create table if not exists likes (
        chat_id int,
        from_user_id int,
        to_user_id int,
        primary key (chat_id, from_user_id)
    )
    """,
    (),
)

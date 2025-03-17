import sqlite3

database_name = "/data/likes.db"


def commit_query(query, args):
    with sqlite3.connect(database_name) as connection:
        connection.execute(query, args)
        connection.commit()


def fetch_number(query, args):
    with sqlite3.connect(database_name) as connection:
        return connection.execute(query, args).fetchone()[0]


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
        update likes 
        set to_user_id = ?
        where chat_id = ?
        and from_user_id = ?
        """,
        (to_user_id, chat_id, from_user_id),
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

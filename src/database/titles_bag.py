import sqlite3

from database.utils import commit_query, database_name, fetch_number


def commit_save_title(chat_id, user_id, user_title):
    commit_query(
        "insert into titles_bag (chat_id, user_id, user_title) values (?, ?, ?)",
        (chat_id, user_id, user_title),
    )


def commit_remove_title(chat_id, user_id, user_title):
    commit_query(
        """
        delete from titles_bag
        where chat_id = ?
          and user_id = ?
          and user_title = ?
        """,
        (chat_id, user_id, user_title),
    )


def get_user_titles_bag(chat_id, user_id):
    with sqlite3.connect(database_name) as connection:
        return connection.execute(
            """
            select id, user_title
            from titles_bag
            where chat_id = ?
            and user_id = ?
            """,
            (chat_id, user_id),
        ).fetchall()


def get_title_in_bag(titles_bag_id):
    return fetch_number(
        """
        select user_title
        from titles_bag
        where id = ?
        """,
        (titles_bag_id,),
    )


def commit_remove_title_in_bag(titles_bag_id):
    commit_query(
        """
        delete from titles_bag
        where id = ?
        """,
        (titles_bag_id,),
    )


commit_query(
    """
    create table if not exists titles_bag (
        id integer primary key autoincrement,
        chat_id int,
        user_id int,
        user_title text
    )
    """,
    (),
)

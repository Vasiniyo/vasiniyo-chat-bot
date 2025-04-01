from database.utils import commit_query, fetch_number


def is_day_passed(chat_id, user_id):
    return fetch_number(
        """
       select date('now', 'localtime') > date(last_changing, 'unixepoch', 'localtime')
       from titles
       where chat_id = ?
       and user_id = ?
    """,
        (chat_id, user_id),
    )


def commit_dice_roll(chat_id, user_id):
    commit_query(
        """
        insert into titles (chat_id, user_id, last_changing) values (?, ?, 0)
        on conflict (chat_id, user_id) do update set last_changing = strftime('%s', 'now');
        """,
        (chat_id, user_id),
    )


commit_query(
    """
    create table if not exists titles (
        chat_id int,
        user_id int,
        last_changing int default (strftime('%s', 'now')),
        primary key (chat_id, user_id)
    )
    """,
    (),
)

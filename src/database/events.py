from database.utils import commit_query, fetch_number


def get_last_winner(chat_id, event_id):
    return fetch_number(
        """
       select winner_user_id
       from events
       where chat_id = ?
       and event_id = ?
       order by last_played desc
       limit 1
    """,
        (chat_id, event_id),
    )


def is_day_passed(chat_id, event_id):
    return fetch_number(
        """
       select date('now', 'localtime') > date(max(last_played), 'unixepoch', 'localtime')
       from events
       where chat_id = ?
       and event_id = ?
       group by chat_id, event_id
    """,
        (chat_id, event_id),
    )


def commit_win(chat_id, user_id, event_id):
    commit_query(
        """
        insert into events (chat_id, winner_user_id, event_id, last_played) values (?, ?, ?, strftime('%s', 'now'))
        on conflict do nothing
        """,
        (chat_id, user_id, event_id),
    )


commit_query(
    """
    create table if not exists events (
        chat_id int,
        winner_user_id int,
        event_id int,
        last_played int default (strftime('%s', 'now')),
        primary key (chat_id, winner_user_id, event_id, last_played)
    )
    """,
    (),
)

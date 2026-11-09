create table if not exists likes (
    chat_id int,
    from_user_id int,
    to_user_id int,
    primary key (chat_id, from_user_id)
);

create table if not exists titles (
    chat_id int,
    user_id int,
    user_title text,
    last_changing int default (strftime('%s', 'now')),
    primary key (chat_id, user_id)
);

create table if not exists titles_bag (
    id integer primary key autoincrement,
    chat_id int,
    user_id int,
    user_title text
);

create table if not exists events (
    chat_id int,
    winner_user_id int,
    event_id int,
    last_played int default (strftime('%s', 'now')),
    primary key (chat_id, winner_user_id, event_id, last_played)
);

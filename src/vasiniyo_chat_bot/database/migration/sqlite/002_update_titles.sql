alter table titles_bag rename to titles_bag_old;
alter table titles rename to titles_old;

create table titles_bag (
    id integer primary key autoincrement,
    chat_id int,
    user_id int,
    user_title text,
    is_inventory boolean
);

create unique index idx_unique_active_title
on titles_bag (chat_id, user_id)
where not is_inventory;

create table titles_states (
    user_id int,
    chat_id int,
    last_changing int default (strftime('%s', 'now')),
    primary key (user_id, chat_id)
);

insert into titles_bag (chat_id, user_id, user_title, is_inventory)
select chat_id, user_id, user_title, false
from titles_old
union all
select chat_id, user_id, user_title, true
from titles_bag_old;


insert into titles_states (user_id, chat_id, last_changing)
select user_id, chat_id, last_changing
from titles_old;

drop table titles_bag_old;
drop table titles_old;

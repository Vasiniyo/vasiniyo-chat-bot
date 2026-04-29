from dataclasses import replace
from sqlite3 import Connection

from vasiniyo_chat_bot.database.sqlite.dao.titles_bag_dao import TitlesBagDAO
from vasiniyo_chat_bot.database.sqlite.dao.titles_states_dao import TitlesStatesDAO
from vasiniyo_chat_bot.database.sqlite.entity.title_bag_entity import TitlesBagEntity
from vasiniyo_chat_bot.database.sqlite.repository.dto import SqliteDatabaseSettings
from vasiniyo_chat_bot.database.sqlite.repository.sqlite_repository import (
    SqliteRepository,
)
from vasiniyo_chat_bot.module.likes.dto import Leaderboard, LeaderboardRow
from vasiniyo_chat_bot.module.titles.titles_repository import TitlesRepository


class SqliteTitlesRepository(SqliteRepository, TitlesRepository):
    def __init__(
        self,
        titles_states_dao: TitlesStatesDAO,
        titles_bag_dao: TitlesBagDAO,
        settings: SqliteDatabaseSettings,
    ):
        super().__init__(settings)
        self._titles_states_dao = titles_states_dao
        self._titles_bag_dao = titles_bag_dao

    def init_title(self, chat_id: int, user_id: int, user_title: str) -> str | None:
        def _tx(conn: Connection) -> str | None:
            if self._titles_bag_dao.find_current(conn, chat_id, user_id):
                return None
            self._titles_states_dao.save(conn, chat_id, user_id)

            titles_entity = self._titles_bag_dao.save(
                conn,
                TitlesBagEntity(
                    chat_id=chat_id,
                    user_id=user_id,
                    user_title=user_title,
                    is_inventory=False,
                ),
            )
            return titles_entity.user_title

        return self.transaction(_tx)

    def update_last_changing(self, chat_id: int, user_id: int) -> None:
        self.transaction(
            lambda conn: self._titles_states_dao.update_last_changing(
                conn, chat_id=chat_id, user_id=user_id
            )
        )

    def find_user_title(self, chat_id: int, user_id: int) -> str | None:
        def _tx(conn: Connection) -> str | None:
            entity = self._titles_bag_dao.find_current(conn, chat_id, user_id)
            return entity.user_title if entity else None

        return self.transaction(_tx)

    def get_user_titles(self, chat_id: int) -> list[TitlesBagEntity]:
        return self.transaction(
            lambda conn: self._titles_bag_dao.get_titles_by_chat(conn, chat_id)
        )

    def get_user_titles_bag(self, chat_id: int, user_id: int) -> Leaderboard:
        def _tx(conn: Connection) -> list[TitlesBagEntity]:
            return self._titles_bag_dao.get_by_chat_and_user(
                conn, chat_id, user_id, True
            )

        return Leaderboard(
            chat_id=chat_id,
            rows=sorted(
                (
                    LeaderboardRow(
                        user_id=bag.user_id, value=(bag.id, bag.user_id, bag.user_title)
                    )
                    for bag in self.transaction(_tx)
                ),
                key=lambda r: r.value[-1],
            ),
        )

    def get_title_after_touch(self, chat_id: int, user_id: int) -> str | None:
        def _tx(conn: Connection):
            self._titles_states_dao.update_last_changing(conn, chat_id, user_id)
            return self._titles_bag_dao.find_current(conn, chat_id, user_id).user_title

        return self.transaction(_tx)

    def is_day_passed(self, chat_id: int, user_id: int) -> bool:
        return self.transaction(
            lambda conn: self._titles_states_dao.is_day_passed(conn, chat_id, user_id)
        )

    def set_current(self, chat_id: int, user_id: int, title_bag_id: int) -> str | None:
        def _tx(conn: Connection) -> str | None:
            target = self._titles_bag_dao.find_by_id(conn, title_bag_id)
            if not target:
                return None
            if not (
                target.chat_id == chat_id
                and target.user_id == user_id
                and target.is_inventory
            ):
                return None
            current = self._titles_bag_dao.find_current(conn, chat_id, user_id)
            if current:
                self._titles_bag_dao.save(conn, replace(current, is_inventory=True))
            entity = self._titles_bag_dao.save(
                conn, replace(target, is_inventory=False)
            )
            return entity.user_title

        return self.transaction(_tx)

    def rotate_title(self, chat_id: int, user_id: int, title: str) -> str:
        def _tx(conn: Connection) -> str:
            current = self._titles_bag_dao.find_current(conn, chat_id, user_id)
            self._titles_bag_dao.save(conn, replace(current, is_inventory=True))
            entity = self._titles_bag_dao.save(
                conn,
                TitlesBagEntity(
                    chat_id=chat_id,
                    user_id=user_id,
                    user_title=title,
                    is_inventory=False,
                ),
            )
            self._titles_states_dao.update_last_changing(conn, chat_id, user_id)
            return entity.user_title

        return self.transaction(_tx)

    def steal_logic(
        self, chat_id, user_id: int, title_id: int
    ) -> tuple[tuple[int | None, str | None], tuple[int | None, str | None]]:
        def _tx(
            conn: Connection,
        ) -> tuple[tuple[int | None, str | None], tuple[int | None, str | None]]:
            target_title = self._titles_bag_dao.find_by_id(conn, title_id)
            if target_title is None or target_title.user_id == user_id:
                return (user_id, None), (None, None)
            self._titles_states_dao.update_last_changing(conn, chat_id, user_id)
            self._titles_states_dao.save(conn, chat_id, target_title.user_id)
            cur_user_title = self._titles_bag_dao.find_current(conn, chat_id, user_id)
            if cur_user_title:
                old_user_title = replace(cur_user_title, is_inventory=True)
                self._titles_bag_dao.save(conn, old_user_title)
            next_user_title = replace(target_title, user_id=user_id, is_inventory=False)
            self._titles_bag_dao.save(conn, next_user_title)
            if target_title.is_inventory:
                cur_target_title = self._titles_bag_dao.find_current(
                    conn, chat_id, target_title.user_id
                )
                if not cur_target_title:
                    target_res = (target_title.user_id, None)
                else:
                    target_res = (cur_target_title.user_id, cur_target_title.user_title)
                return (
                    (next_user_title.user_id, next_user_title.user_title),
                    target_res,
                )
            target_user_id = target_title.user_id
            target_inventory_titles = self._titles_bag_dao.get_by_chat_and_user(
                conn, chat_id, target_user_id, True
            )
            if not target_inventory_titles:
                self._titles_states_dao.remove(conn, chat_id, target_user_id)
                return (
                    (next_user_title.user_id, next_user_title.user_title),
                    (target_title.user_id, None),
                )
            next_target_title = replace(target_inventory_titles[0], is_inventory=False)
            self._titles_bag_dao.save(conn, next_target_title)
            return (
                (next_user_title.user_id, next_user_title.user_title),
                (next_target_title.user_id, next_target_title.user_title),
            )

        return self.transaction(_tx)

    def exists(self, chat_id: int, user_id: int, title_bag_id: int):
        def _tx(conn: Connection) -> bool:
            entity = self._titles_bag_dao.find_by_id(conn, title_bag_id)
            return entity and entity.chat_id == chat_id and entity.user_id == user_id

        return self.transaction(_tx)

    def get_users_by_chat(self, chat_id) -> set[int]:
        def _tx(conn: Connection) -> set[int]:
            return {
                entity.user_id
                for entity in self._titles_bag_dao.get_by_chat(conn, chat_id)
            }

        return self.transaction(_tx)

    def set_inventory(
        self, chat_id: int, user_id: int, title_bag_id: int
    ) -> str | None:
        def _tx(conn: Connection) -> str | None:
            entity = self._titles_bag_dao.find_by_id(conn, title_bag_id)
            if not entity:
                return None
            if entity.chat_id != chat_id or not entity.is_inventory:
                return None
            self._titles_bag_dao.save(
                conn, replace(entity, user_id=user_id, is_inventory=True)
            )
            return entity.user_title

        return self.transaction(_tx)

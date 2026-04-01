from sqlite3 import Connection

from vasiniyo_chat_bot.database.sqlite.dao.titles_bag_dao import TitlesBagDAO
from vasiniyo_chat_bot.database.sqlite.dao.titles_dao import TitlesDAO
from vasiniyo_chat_bot.database.sqlite.entity.title_bag_entity import TitlesBagEntity
from vasiniyo_chat_bot.database.sqlite.entity.title_entity import TitleEntity
from vasiniyo_chat_bot.database.sqlite.repository.dto import SqliteDatabaseSettings
from vasiniyo_chat_bot.database.sqlite.repository.sqlite_repository import (
    SqliteRepository,
)
from vasiniyo_chat_bot.module.likes.dto import Leaderboard, LeaderboardRow
from vasiniyo_chat_bot.module.titles.titles_repository import TitlesRepository


class SqliteTitlesRepository(SqliteRepository, TitlesRepository):
    def __init__(
        self,
        titlesDao: TitlesDAO,
        titles_bag_dao: TitlesBagDAO,
        settings: SqliteDatabaseSettings,
    ):
        super().__init__(settings)
        self._titles_dao = titlesDao
        self._titles_bag_dao = titles_bag_dao

    def init_title(self, chat_id: int, user_id: int, user_title: str) -> str | None:
        def _tx(conn: Connection) -> str | None:
            if self._titles_dao.find_title(conn, chat_id, user_id):
                return None
            titles_entity = self._titles_dao.save(
                conn, chat_id=chat_id, user_id=user_id, user_title=user_title
            )
            return titles_entity.user_title

        return self.transaction(_tx)

    def update_last_changing(self, chat_id: int, user_id: int) -> None:
        self.transaction(
            lambda conn: self._titles_dao.update_last_changing(
                conn, chat_id=chat_id, user_id=user_id
            )
        )

    def find_user_title(self, chat_id: int, user_id: int) -> str | None:
        return self.transaction(
            lambda conn: self._titles_dao.find_title(conn, chat_id, user_id)
        )

    def get_user_titles(self, chat_id: int) -> Leaderboard:
        def _tx(conn: Connection) -> list[TitleEntity]:
            return self._titles_dao.get_titles_by_chat(conn, chat_id)

        return Leaderboard(
            chat_id=chat_id,
            rows=[
                LeaderboardRow(user_id=entity.user_id, value=entity.user_title)
                for entity in self.transaction(_tx)
            ],
        )

    def get_user_titles_bag(self, chat_id: int, user_id: int) -> Leaderboard:
        def _tx(conn: Connection) -> list[TitlesBagEntity]:
            return self._titles_bag_dao.get_by_chat_and_user(conn, chat_id, user_id)

        return Leaderboard(
            chat_id=chat_id,
            rows=[
                LeaderboardRow(user_id=bag.user_id, value=(bag.id, bag.user_title))
                for bag in self.transaction(_tx)
            ],
        )

    def get_title_after_touch(self, chat_id: int, user_id: int) -> str | None:
        def _tx(conn: Connection):
            self._titles_dao.update_last_changing(conn, chat_id, user_id)
            return self._titles_dao.find_title(conn, chat_id, user_id)

        return self.transaction(_tx)

    def is_day_passed(self, chat_id: int, user_id: int) -> bool:
        return self.transaction(
            lambda conn: self._titles_dao.is_day_passed(conn, chat_id, user_id)
        )

    def swap_title(self, chat_id: int, user_id: int, title_bag_id: int) -> str | None:
        def _tx(conn: Connection) -> str | None:
            current_title = self._titles_dao.find_title(conn, chat_id, user_id)
            titles_bag = self._titles_bag_dao.find_by_id(conn, title_bag_id)
            if titles_bag is None:
                return None
            self._titles_dao.update_user_title(
                conn, chat_id, user_id, titles_bag.user_title
            )
            self._titles_bag_dao.remove_by_id(conn, title_bag_id)
            if current_title:
                self._titles_bag_dao.save(conn, chat_id, user_id, current_title)
            return self._titles_dao.find_title(conn, chat_id, user_id)

        return self.transaction(_tx)

    def rotate_title(self, chat_id: int, user_id: int, title: str):
        def _tx(conn: Connection) -> str:
            current_title = self._titles_dao.find_title(conn, chat_id, user_id)
            self._titles_bag_dao.save(conn, chat_id, user_id, current_title)
            title_entity = self._titles_dao.save(conn, chat_id, user_id, title)
            return title_entity.user_title

        return self.transaction(_tx)

    def steal_logic(
        self, chat_id, actor_id: int, target_id: int
    ) -> tuple[str | None, str | None]:
        def _tx(conn: Connection) -> tuple[str | None, str | None]:
            actor_title = self._titles_dao.find_title(conn, chat_id, actor_id)
            target_title = self._titles_dao.find_title(conn, chat_id, target_id)
            if target_title is None:
                return actor_title, None
            self._titles_dao.update_user_title_and_last_changing(
                conn, chat_id, actor_id, target_title
            )
            if actor_title:
                self._titles_bag_dao.save(conn, chat_id, actor_id, actor_title)
            titles_bag = self._titles_bag_dao.get_by_chat_and_user(
                conn, chat_id, target_id
            )
            if not titles_bag:
                self._titles_dao.remove(conn, chat_id, target_id)
                return target_title, None
            titles_bag_entity = titles_bag[0]
            self._titles_bag_dao.remove_by_id(conn, titles_bag_entity.id)
            title_entity = self._titles_dao.save(
                conn, chat_id, target_id, titles_bag_entity.user_title
            )
            return target_title, title_entity.user_title

        return self.transaction(_tx)

from abc import ABC
from abc import abstractmethod
import logging

from injector import inject
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from vasiniyo_chat_bot.database.migration import sqlite_migration

_logger = logging.getLogger(__name__)


class Database(ABC):
    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url, echo=False)
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)

    @abstractmethod
    def create_tables(self) -> None:
        pass

    def session(self) -> Session:
        return self._session_factory()


@inject
class SqliteDatabase(Database):
    def create_tables(self) -> None:
        with self.session() as session:
            with session.begin():
                sqlite_migration.apply_migrations(session, self._engine)

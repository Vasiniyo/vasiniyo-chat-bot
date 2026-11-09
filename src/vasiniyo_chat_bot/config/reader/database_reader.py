import os

from injector import inject

from vasiniyo_chat_bot.config.dto import Config
from vasiniyo_chat_bot.database.database import Database
from vasiniyo_chat_bot.database.database import SqliteDatabase


@inject
class DatabaseReader:
    def __init__(self, config: Config) -> None:
        self._config = config

    def load(self) -> Database:
        database_type = self._config.section.get("database", {}).get("type", "sqlite")
        if database_type.lower() == "sqlite":
            path = os.environ.get("DATABASE_PATH", "data/database.db")
            database = SqliteDatabase(f"sqlite:///{path}")
            database.create_tables()
            return database
        raise ValueError(f"Unknown database type: {database_type}")

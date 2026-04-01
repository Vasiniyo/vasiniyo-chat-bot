import os

from vasiniyo_chat_bot.config.dto import DatabaseSettings
from vasiniyo_chat_bot.database.sqlite.repository.dto import SqliteDatabaseSettings


class DatabaseReader:
    def __init__(self, section: dict[str, any]) -> None:
        self._section = section

    def load(self) -> DatabaseSettings:
        database_type = self._section.get("database", {}).get("type", "sqlite")
        if database_type.lower() == "sqlite":
            return SqliteDatabaseSettings(
                database_path=os.environ.get("DATABASE_PATH", "data/database.db")
            )
        raise ValueError(f"Unknown database type: {database_type}")

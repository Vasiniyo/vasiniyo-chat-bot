from dataclasses import dataclass

from vasiniyo_chat_bot.config.dto import DatabaseSettings


@dataclass(frozen=True)
class SqliteDatabaseSettings(DatabaseSettings):
    database_path: str

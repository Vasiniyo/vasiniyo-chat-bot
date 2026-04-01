from __future__ import annotations

import sqlite3
from sqlite3 import Connection
import threading
from typing import Callable, TypeVar

from vasiniyo_chat_bot.database.sqlite.repository.dto import SqliteDatabaseSettings

T = TypeVar("T")
R = TypeVar("R", bound="SqliteRepository")


class SqliteRepository:
    def __init__(self, settings: SqliteDatabaseSettings) -> None:
        self.database_name = settings.database_path
        self._tx_connection = threading.local()

    def transaction(self, block: Callable[[Connection], T]) -> T:
        exists_conn = getattr(self._tx_connection, "conn", None)
        if exists_conn:
            return block(exists_conn)
        conn = sqlite3.connect(self.database_name)
        try:
            self._tx_connection.conn = conn
            try:
                result = block(conn)
                conn.commit()
                return result
            except:
                conn.rollback()
                raise
        finally:
            conn.close()
            del self._tx_connection.conn

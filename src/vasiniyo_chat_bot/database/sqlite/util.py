from sqlite3 import Connection, Cursor


class SQLiteDao:
    @staticmethod
    def execute(conn: Connection, query: str, args: tuple) -> Cursor:
        return conn.execute(query, args)

    @staticmethod
    def fetchone(conn: Connection, query: str, args: tuple) -> any:
        return conn.execute(query, args).fetchone()

    @staticmethod
    def fetchall(conn: Connection, query: str, args: tuple) -> list:
        return conn.execute(query, args).fetchall()

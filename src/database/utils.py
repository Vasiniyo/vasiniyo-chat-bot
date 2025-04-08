import sqlite3

database_name = "/data/database.db"
head = lambda l: l[0] if l else None


def commit_query(query, args):
    with sqlite3.connect(database_name) as connection:
        connection.execute(query, args)
        connection.commit()


def fetch_number(query, args):
    with sqlite3.connect(database_name) as connection:
        return head(connection.execute(query, args).fetchone())


def is_column_exist(table, column):
    query = """
            select count(*) > 0
            from pragma_table_info('{}') WHERE name=?;
        """
    return fetch_number(query.format(table), (column,))

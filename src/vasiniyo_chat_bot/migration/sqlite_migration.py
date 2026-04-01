import logging
import sqlite3

from vasiniyo_chat_bot import migration

logger = logging.getLogger(__name__)


def _get_applied_versions(conn):
    conn.execute("""
        create table if not exists schema_migrations (
            version integer primary key
        );
        """)
    rows = conn.execute("select version from schema_migrations").fetchall()
    return {row[0] for row in rows}


def apply_migrations(database_path):
    with sqlite3.connect(database_path) as conn:
        applied = _get_applied_versions(conn)
        try:
            files = sorted(
                [file for file in migration.sqlite() if file.name.endswith(".sql")],
                key=lambda f: int(f.name.split("_")[0]),
            )
        except Exception:
            logger.exception("Invalid migrations, expected format: {digits}_{name}.sql")
            raise
        for file in files:
            version = int(file.name.split("_")[0])
            if version in applied:
                continue
            logger.info(f"Applying migration", extra={"sql_filename": file.name})
            with conn:
                try:
                    conn.executescript(file.read_text())
                    conn.execute(
                        """
                        insert into schema_migrations (version)
                        values (?)
                        """,
                        (version,),
                    )
                except Exception:
                    logger.exception(
                        f"Failed migration", extra={"sql_filename": file.name}
                    )
                    raise

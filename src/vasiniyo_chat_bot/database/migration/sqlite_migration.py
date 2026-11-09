import logging

from sqlalchemy import Engine
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.orm import Session

from vasiniyo_chat_bot.database import migration
from vasiniyo_chat_bot.database.entity.schema_migrations import SchemaMigrations

_logger = logging.getLogger(__name__)


def apply_migrations(session: Session, engine: Engine) -> None:
    SchemaMigrations.__table__.create(bind=engine, checkfirst=True)
    applied = {
        version for version in session.scalars(select(SchemaMigrations.version)).all()
    }
    try:
        files = sorted(
            [file for file in migration.sqlite_files() if file.name.endswith(".sql")],
            key=lambda f: int(f.name.split("_")[0]),
        )
    except Exception:
        _logger.exception("Invalid migrations, expected format: {digits}_{name}.sql")
        raise
    for file in files:
        version = int(file.name.split("_")[0])
        if version in applied:
            continue
        _logger.info(f"Applying migration", extra={"sql_filename": file.name})
        try:
            statements = [
                statement.strip()
                for statement in file.read_text().split(";")
                if statement.strip()
            ]
            for statement in statements:
                session.execute(text(statement))
            session.add(SchemaMigrations(version=version))
        except Exception:
            _logger.exception(f"Failed migration", extra={"sql_filename": file.name})
            raise

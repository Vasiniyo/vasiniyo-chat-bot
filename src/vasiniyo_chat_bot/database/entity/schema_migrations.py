from dataclasses import dataclass

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from vasiniyo_chat_bot.database.repository.base_repository import Entity


@dataclass
class SchemaMigrations(Entity):
    __tablename__ = "schema_migrations"
    version: Mapped[int] = mapped_column(primary_key=True)

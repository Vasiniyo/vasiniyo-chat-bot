from dataclasses import dataclass

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from vasiniyo_chat_bot.database.repository.base_repository import Entity


@dataclass
class EventEntity(Entity):
    __tablename__ = "events"
    chat_id: Mapped[int] = mapped_column(primary_key=True)
    winner_user_id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(primary_key=True)
    last_played: Mapped[int] = mapped_column(primary_key=True)


@dataclass(frozen=True)
class WinnerStats:
    user_id: int
    score: int

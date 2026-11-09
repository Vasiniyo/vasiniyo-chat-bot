from typing import Sequence

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from vasiniyo_chat_bot.database.entity import EventEntity
from vasiniyo_chat_bot.database.entity.event_entity import WinnerStats
from vasiniyo_chat_bot.database.repository.base_repository import BaseRepository


class EventsRepository(BaseRepository):
    @staticmethod
    def get_last_winner(session: Session, chat_id: int, event_id: int) -> int | None:
        return session.scalar(
            select(EventEntity.winner_user_id)
            .where(EventEntity.chat_id == chat_id, EventEntity.event_id == event_id)
            .order_by(EventEntity.last_played.desc())
            .limit(1)
        )

    @staticmethod
    def fetch_top(
        session: Session, chat_id: int, event_id: int, limit: int
    ) -> Sequence[WinnerStats]:
        return [
            WinnerStats(user_id=row.winner_user_id, score=row.winner_count)
            for row in session.execute(
                select(
                    EventEntity.winner_user_id.label("winner_user_id"),
                    func.count().label("winner_count"),
                )
                .where(EventEntity.chat_id == chat_id, EventEntity.event_id == event_id)
                .group_by(EventEntity.winner_user_id)
                .order_by(func.count().desc())
                .limit(limit)
            )
        ]

    @staticmethod
    def is_day_passed(session: Session, chat_id: int, event_id: int) -> bool:
        result = session.scalar(
            select(
                func.date("now", "localtime")
                > func.date(func.max(EventEntity.last_played), "unixepoch", "localtime")
            )
            .where(EventEntity.chat_id == chat_id, EventEntity.event_id == event_id)
            .group_by(EventEntity.chat_id, EventEntity.event_id)
        )
        return bool(result) if result is not None else True

from typing import Sequence

from sqlalchemy import func
from sqlalchemy import inspect
from sqlalchemy import select
from sqlalchemy.orm import Session

from vasiniyo_chat_bot.database.entity.like_entity import LikeEntity
from vasiniyo_chat_bot.database.entity.like_entity import LikeStats
from vasiniyo_chat_bot.database.repository.base_repository import BaseRepository


class LikesRepository(BaseRepository):
    @staticmethod
    def find_by_id(
        session: Session, chat_id: int, from_user_id: int
    ) -> LikeEntity | None:
        return session.get(
            LikeEntity, {"chat_id": chat_id, "from_user_id": from_user_id}
        )

    @staticmethod
    def get_leaderboard(
        session: Session, chat_id: int, limit: int
    ) -> Sequence[LikeStats]:
        return [
            LikeStats(user_id=row.user_id, like_count=row.like_count)
            for row in session.execute(
                select(
                    LikeEntity.to_user_id.label("user_id"),
                    func.count().label("like_count"),
                )
                .where(LikeEntity.chat_id == chat_id)
                .group_by(LikeEntity.to_user_id)
                .order_by(func.count().desc())
                .limit(limit)
            )
        ]

    @staticmethod
    def set_like(session: Session, entity: LikeEntity) -> LikeEntity:
        to_user_id = entity.to_user_id
        if inspect(entity).session is not session:
            existing = LikesRepository.find_by_id(
                session, entity.chat_id, entity.from_user_id
            )
            if existing is None:
                LikesRepository.save(session, entity)
            else:
                entity = existing
        entity.to_user_id = to_user_id
        return entity

    @staticmethod
    def count_by_chat_and_to_user(
        session: Session, chat_id: int, to_user_id: int
    ) -> int:
        result = session.scalar(
            select(func.count(LikeEntity.to_user_id)).where(
                LikeEntity.chat_id == chat_id, LikeEntity.to_user_id == to_user_id
            )
        )
        return result or 0

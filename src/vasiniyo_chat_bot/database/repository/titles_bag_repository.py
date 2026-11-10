from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from vasiniyo_chat_bot.database.entity import TitlesBagEntity
from vasiniyo_chat_bot.database.repository.base_repository import BaseRepository


class TitlesBagRepository(BaseRepository):
    @staticmethod
    def find_by_id(session: Session, title_id: int) -> TitlesBagEntity | None:
        return session.get(TitlesBagEntity, {"id": title_id})

    @staticmethod
    def get_by_chat(session: Session, chat_id: int) -> Sequence[TitlesBagEntity]:
        return session.scalars(
            select(TitlesBagEntity).where(TitlesBagEntity.chat_id == chat_id)
        ).all()

    @staticmethod
    def get_inventory_titles(
        session: Session, chat_id: int, user_id: int
    ) -> Sequence[TitlesBagEntity]:
        return session.scalars(
            select(TitlesBagEntity).where(
                TitlesBagEntity.chat_id == chat_id,
                TitlesBagEntity.user_id == user_id,
                TitlesBagEntity.is_inventory,
            )
        ).all()

    @staticmethod
    def find_active_title(
        session: Session, chat_id: int, user_id: int
    ) -> TitlesBagEntity | None:
        return session.scalars(
            select(TitlesBagEntity).where(
                TitlesBagEntity.chat_id == chat_id,
                TitlesBagEntity.user_id == user_id,
                TitlesBagEntity.is_inventory.is_(False),
            )
        ).one_or_none()

    @staticmethod
    def set_active(session: Session, entity: TitlesBagEntity) -> None:
        if entity.is_active:
            return
        if current_active := TitlesBagRepository.find_active_title(
            session, entity.chat_id, entity.user_id
        ):
            current_active.is_inventory = True
            session.flush()
        entity.is_inventory = False

    @staticmethod
    def set_inventory(session: Session, entity: TitlesBagEntity) -> None:
        if entity.is_inventory:
            return
        titles = TitlesBagRepository.get_inventory_titles(
            session, entity.chat_id, entity.user_id
        )
        if titles:
            titles[0].is_inventory = False
            session.flush()
        entity.is_inventory = True

    @staticmethod
    def transfer(session: Session, entity: TitlesBagEntity, new_user_id: int) -> None:
        TitlesBagRepository.set_inventory(session, entity)
        entity.user_id = new_user_id

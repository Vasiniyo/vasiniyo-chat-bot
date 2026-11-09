from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from vasiniyo_chat_bot.database.entity.title_entity import TitlesStateEntity
from vasiniyo_chat_bot.database.repository.base_repository import BaseRepository


class TitlesStatesRepository(BaseRepository):
    @staticmethod
    def find_by_id(
        session: Session, chat_id: int, user_id: int
    ) -> TitlesStateEntity | None:
        return session.get(TitlesStateEntity, {"chat_id": chat_id, "user_id": user_id})

    @staticmethod
    def consume_daily_roll(session: Session, entity: TitlesStateEntity) -> None:
        entity.last_changing = func.strftime("%s", "now")

    @staticmethod
    def set_extra_rolls(
        session: Session, entity: TitlesStateEntity, extra_rolls: int
    ) -> None:
        entity.extra_rolls = extra_rolls

    @staticmethod
    def is_day_passed(session: Session, entity: TitlesStateEntity) -> bool:
        result = session.scalar(
            select(func.date("now") > func.date(entity.last_changing, "unixepoch"))
        )
        return bool(result) if result is not None else True

from typing import TypeVar

from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Session

E = TypeVar("E", bound="Entity")


class Entity(DeclarativeBase):
    pass


class BaseRepository:
    @staticmethod
    def save(session: Session, entity: E) -> E:
        state = inspect(entity)
        if state.session is session:
            return entity
        if state.transient:
            session.add(entity)
            return entity
        raise ValueError(
            "Entity must either be a new object or be loaded "
            "from the current SQLAlchemy Session"
        )

    @staticmethod
    def remove(session: Session, entity: E) -> bool:
        state = inspect(entity)
        if state.session is not session:
            return False
        session.delete(entity)
        return True

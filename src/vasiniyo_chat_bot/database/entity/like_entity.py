from dataclasses import dataclass

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from vasiniyo_chat_bot.database.repository.base_repository import Entity


@dataclass
class LikeEntity(Entity):
    __tablename__ = "likes"
    chat_id: Mapped[int] = mapped_column(primary_key=True)
    from_user_id: Mapped[int] = mapped_column(primary_key=True)
    to_user_id: Mapped[int] = mapped_column()


@dataclass(frozen=True)
class LikeStats:
    user_id: int
    like_count: int

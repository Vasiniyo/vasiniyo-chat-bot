from dataclasses import dataclass

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from vasiniyo_chat_bot.database.repository.base_repository import Entity


@dataclass
class TitlesBagEntity(Entity):
    __tablename__ = "titles_bag"
    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column()
    user_id: Mapped[int] = mapped_column()
    user_title: Mapped[str] = mapped_column()
    is_inventory: Mapped[bool] = mapped_column()

    @property
    def is_active(self) -> bool:
        return not self.is_inventory

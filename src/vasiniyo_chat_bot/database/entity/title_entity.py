from sqlalchemy import text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from vasiniyo_chat_bot.database.repository.base_repository import Entity


class TitlesStateEntity(Entity):
    __tablename__ = "titles_states"
    chat_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(primary_key=True)
    last_changing: Mapped[int] = mapped_column(
        server_default=text("(strftime('%s', 'now'))")
    )
    extra_rolls: Mapped[int] = mapped_column(server_default=text("0"))

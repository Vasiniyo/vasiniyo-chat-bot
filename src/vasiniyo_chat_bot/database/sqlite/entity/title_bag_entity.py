from dataclasses import dataclass


@dataclass(frozen=True)
class TitlesBagEntity:
    chat_id: int
    user_id: int
    user_title: str
    is_inventory: bool
    id: int | None = None

from dataclasses import dataclass


@dataclass(frozen=True)
class TitleEntity:
    chat_id: int
    user_id: int
    user_title: str
    last_changing: int

from dataclasses import dataclass


@dataclass(frozen=True)
class TitlesStateEntity:
    chat_id: int
    user_id: int
    last_changing: int

from dataclasses import dataclass


@dataclass
class LikeEntity:
    chat_id: int
    from_user_id: int
    to_user_id: int

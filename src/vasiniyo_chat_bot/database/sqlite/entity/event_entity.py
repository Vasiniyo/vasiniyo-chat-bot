from dataclasses import dataclass


@dataclass
class EventEntity:
    chat_id: int
    winner_user_id: int
    event_id: int
    last_played: int

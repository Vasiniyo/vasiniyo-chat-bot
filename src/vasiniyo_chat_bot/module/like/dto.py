from dataclasses import dataclass


@dataclass(frozen=True)
class Like:
    current_likes: int

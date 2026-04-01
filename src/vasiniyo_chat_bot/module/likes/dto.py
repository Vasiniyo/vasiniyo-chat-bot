from dataclasses import dataclass


@dataclass(frozen=True)
class LeaderboardRow:
    user_id: int
    value: str | int | tuple[int, str]


@dataclass(frozen=True)
class Leaderboard:
    chat_id: int
    rows: list[LeaderboardRow]


@dataclass(frozen=True)
class Like:
    current_likes: int | None

from typing import Protocol


class EventPlayersService(Protocol):
    def get_players(self, chat_id: int) -> list[int]: ...

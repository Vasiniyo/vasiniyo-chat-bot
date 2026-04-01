import random

from vasiniyo_chat_bot.module.likes.dto import Leaderboard, LeaderboardRow
from vasiniyo_chat_bot.module.play.dto import PlayCategory, PlayStatus, Winner, WinValue
from vasiniyo_chat_bot.module.play.event_player_repository import EventPlayersRepository
from vasiniyo_chat_bot.module.play.events_repository import EventsRepository
from vasiniyo_chat_bot.safely_bot_utils import daily_hash


class PlayService:
    _play_event_id = 0

    def __init__(
        self,
        event_players_repository: EventPlayersRepository,
        event_repository: EventsRepository,
        categories: list[PlayCategory],
    ):
        self.event_repository = event_repository
        self.event_players_repository = event_players_repository
        self._categories = categories

    def get_daily_score(self, chat_id: int, user_id: int) -> PlayStatus | None:
        category = self.get_current_playable_category(chat_id)
        return PlayStatus(
            category=category, value=self._get_value_by_user_id(category, user_id)
        )

    def handle_winner(self, leaderboard: Leaderboard) -> Winner | None:
        scores = leaderboard.rows
        if not scores:
            return None
        chat_id = leaderboard.chat_id
        if not self.event_repository.is_day_passed(chat_id, self._play_event_id):
            winner_id = self.event_repository.get_last_winner(
                chat_id, self._play_event_id
            )
            win_score = next(
                (score for score in scores if score.user_id == winner_id), None
            )
            if win_score:
                return Winner(
                    winner_id=win_score.user_id,
                    value=win_score.value,
                    first_in_day=False,
                )
        winner_id, value = scores[0].user_id, scores[0].value
        self.event_repository.insert_winner(chat_id, winner_id, self._play_event_id)
        return Winner(winner_id=winner_id, value=value, first_in_day=True)

    def handle_top_winners(self, chat_id: int, limit: int) -> Leaderboard:
        return self.event_repository.get_leaderboard(
            chat_id, self._play_event_id, limit
        )

    def get_players(
        self,
        category: PlayCategory,
        chat_id: int,
        seed: int = 0,
        extra_players: list[int] | None = None,
    ) -> Leaderboard:
        players = {
            *self.event_players_repository.get_players(chat_id),
            *(extra_players if extra_players is not None else {}),
        }
        scores = [
            LeaderboardRow(
                user_id=user_id,
                value=self._get_value_by_user_id(category, user_id, seed),
            )
            for user_id in players
        ]
        match category.win_value:
            case WinValue.EXACT:
                scores.sort(
                    key=lambda score: abs(score.value - category.win_value.value)
                )
            case WinValue.MAX:
                scores.sort(key=lambda score: score.value, reverse=True)
            case WinValue.MIN:
                scores.sort(key=lambda score: score.value)
            case _:
                raise ValueError
        return Leaderboard(chat_id=chat_id, rows=scores)

    def get_current_playable_category(
        self, chat_id: int, test: bool = False
    ) -> PlayCategory:
        seed = random.randint(0, 2**32 - 1) if test else daily_hash(chat_id)
        return random.Random(seed).choice(self._categories)

    @staticmethod
    def _get_value_by_user_id(category: PlayCategory, user_id: int, salt: int = 0):
        category_hash = sum(ord(c) for c in category.name)
        seed = daily_hash(user_id + category_hash + salt)
        rng = random.Random(seed)
        return rng.randint(*rng.choice(category.ranges))

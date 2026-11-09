import logging
import random

from injector import inject

from vasiniyo_chat_bot.database.database import Database
from vasiniyo_chat_bot.database.entity import EventEntity
from vasiniyo_chat_bot.database.repository.events_repository import EventsRepository
from vasiniyo_chat_bot.module.dto import Leaderboard
from vasiniyo_chat_bot.module.dto import LeaderboardRow
from vasiniyo_chat_bot.module.play.dto import Event
from vasiniyo_chat_bot.module.play.dto import PlayCategory
from vasiniyo_chat_bot.module.play.dto import PlayStatus
from vasiniyo_chat_bot.module.play.dto import WinValue
from vasiniyo_chat_bot.module.play.dto import Winner
from vasiniyo_chat_bot.module.play.event_player_service import EventPlayersService
from vasiniyo_chat_bot.safely_bot_utils import daily_hash

_logger = logging.getLogger(__name__)


@inject
class PlayService:
    _play_event_id = 0

    def __init__(
        self,
        event_players_service: EventPlayersService,
        event_repository: EventsRepository,
        event: Event,
        database: Database,
    ):
        self._event_repository = event_repository
        self._players_service = event_players_service
        self._categories = event.play_categories
        self._database = database

    def get_daily_score(self, chat_id: int, user_id: int) -> PlayStatus:
        category = self.get_current_playable_category(chat_id)
        return PlayStatus(
            category=category, value=self._get_value_by_user_id(category, user_id)
        )

    def handle_winner(self, leaderboard: Leaderboard) -> Winner | None:
        with self._database.session() as session:
            with session.begin():
                scores = leaderboard.rows
                if not scores:
                    return None
                chat_id = leaderboard.chat_id
                if not self._event_repository.is_day_passed(
                    session, chat_id, self._play_event_id
                ):
                    winner_id = self._event_repository.get_last_winner(
                        session, chat_id, self._play_event_id
                    )
                    win_score = next(
                        (score for score in scores if score.user_id == winner_id), None
                    )
                    if win_score:
                        value = win_score.value
                        if not isinstance(value, int):
                            _logger.warning(
                                "invalid value type, expected int",
                                extra={"value": value},
                            )
                            return None
                        return Winner(
                            winner_id=win_score.user_id, value=value, first_in_day=False
                        )
                winner_id, value = scores[0].user_id, scores[0].value
                self._event_repository.save(
                    session,
                    EventEntity(
                        chat_id=chat_id,
                        winner_user_id=winner_id,
                        event_id=self._play_event_id,
                    ),
                )
                if not isinstance(value, int):
                    _logger.warning(
                        "invalid value type, expected int", extra={"value": value}
                    )
                    return None
                return Winner(winner_id=winner_id, value=value, first_in_day=True)

    def handle_top_winners(self, chat_id: int, limit: int) -> Leaderboard:
        with self._database.session() as session:
            with session.begin():
                return Leaderboard(
                    chat_id=chat_id,
                    rows=[
                        LeaderboardRow(user_id=row.user_id, value=row.score)
                        for row in self._event_repository.fetch_top(
                            session, chat_id, self._play_event_id, limit
                        )
                    ],
                )

    def get_players(
        self,
        category: PlayCategory,
        chat_id: int,
        seed: int = 0,
        extra_players: list[int] | None = None,
    ) -> Leaderboard:
        players = {
            *self._players_service.get_players(chat_id),
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

import logging
import random

from injector import inject

from vasiniyo_chat_bot.module.dto import MessageContext
from vasiniyo_chat_bot.module.play.dto import Winner
from vasiniyo_chat_bot.module.play.play_response_factory import PlayResponseFactory
from vasiniyo_chat_bot.module.play.play_service import PlayService
from vasiniyo_chat_bot.module.renderer import Renderer

_logger = logging.getLogger(__name__)


@inject
class PlayController:
    def __init__(
        self,
        play_service: PlayService,
        response_factory: PlayResponseFactory,
        renderer: Renderer,
    ) -> None:
        self._play_service = play_service
        self._response_factory = response_factory
        self._renderer = renderer

    def handle_play(self, ctx: MessageContext):
        play_status = self._play_service.get_daily_score(ctx.chat_id, ctx.user_id)
        response = self._response_factory.daily_result(play_status)
        self._renderer.send(response, ctx)

    def handle_players(self, ctx: MessageContext):
        category = self._play_service.get_current_playable_category(ctx.chat_id)
        leaderboard = self._play_service.get_players(category, ctx.chat_id)
        response = self._response_factory.players(leaderboard)
        self._renderer.send(response, ctx)

    def handle_winner(self, ctx: MessageContext):
        category = self._play_service.get_current_playable_category(ctx.chat_id)
        leaderboard = self._play_service.get_players(category, ctx.chat_id)
        winner = self._play_service.handle_winner(leaderboard)
        response = (
            self._response_factory.winner(ctx.chat_id, winner, category)
            if winner
            else self._response_factory.winner_not_found()
        )
        self._renderer.send(response, ctx)

    def handle_top_winners(self, ctx: MessageContext):
        leaderboard = self._play_service.handle_top_winners(ctx.chat_id, limit=10)
        response = self._response_factory.leaderboard(leaderboard)
        self._renderer.send(response, ctx)

    def handle_test_new_winner(self, ctx: MessageContext):
        category = self._play_service.get_current_playable_category(ctx.chat_id)
        leaderboard = self._play_service.get_players(
            category, ctx.chat_id, seed=random.randint(0, 1000)
        )
        winner_info = leaderboard.rows[0]
        if not isinstance(winner_info.value, int):
            _logger.warning(
                "invalid winner value, expected type int",
                extra={"value": winner_info.value},
            )
            response = self._response_factory.winner_not_found()
        else:
            winner = Winner(
                winner_id=winner_info.user_id,
                value=winner_info.value,
                first_in_day=True,
            )
            response = self._response_factory.winner(ctx.chat_id, winner, category)
        self._renderer.send(response, ctx)

    def handle_test_new_category(self, ctx: MessageContext):
        category = self._play_service.get_current_playable_category(
            ctx.chat_id, test=True
        )
        leaderboard = self._play_service.get_players(
            category,
            ctx.chat_id,
            seed=random.randint(0, 1000),
            extra_players=[ctx.user_id],
        )
        response = self._response_factory.debug_daily_result(category, leaderboard)
        self._renderer.send(response, ctx)

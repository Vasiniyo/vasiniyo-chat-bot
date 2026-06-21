import random

from vasiniyo_chat_bot.module.dto import UserContext
from vasiniyo_chat_bot.module.play.dto import Winner
from vasiniyo_chat_bot.module.play.play_response_factory import PlayResponseFactory
from vasiniyo_chat_bot.module.play.play_service import PlayService
from vasiniyo_chat_bot.module.renderer import Renderer


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

    def handle_play(self, ctx: UserContext):
        play_status = self._play_service.get_daily_score(ctx.chat_id, ctx.user_id)
        response = self._response_factory.daily_result(play_status)
        self._renderer.send(response, ctx)

    def handle_players(self, ctx: UserContext):
        category = self._play_service.get_current_playable_category(ctx.chat_id)
        leaderboard = self._play_service.get_players(category, ctx.chat_id)
        response = self._response_factory.players(leaderboard)
        self._renderer.send(response, ctx)

    def handle_winner(self, ctx: UserContext):
        category = self._play_service.get_current_playable_category(ctx.chat_id)
        leaderboard = self._play_service.get_players(category, ctx.chat_id)
        winner = self._play_service.handle_winner(leaderboard)
        response = self._response_factory.winner(ctx.chat_id, winner, category)
        self._renderer.send(response, ctx)

    def handle_top_winners(self, ctx: UserContext):
        leaderboard = self._play_service.handle_top_winners(ctx.chat_id, limit=10)
        response = self._response_factory.leaderboard(leaderboard)
        self._renderer.send(response, ctx)

    def handle_test_new_winner(self, ctx: UserContext):
        category = self._play_service.get_current_playable_category(ctx.chat_id)
        leaderboard = self._play_service.get_players(
            category, ctx.chat_id, seed=random.randint(0, 1000)
        )
        winner = Winner(
            winner_id=leaderboard.rows[0].user_id,
            value=leaderboard.rows[0].value,
            first_in_day=True,
        )
        response = self._response_factory.winner(ctx.chat_id, winner, category)
        self._renderer.send(response, ctx)

    def handle_test_new_category(self, ctx: UserContext):
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

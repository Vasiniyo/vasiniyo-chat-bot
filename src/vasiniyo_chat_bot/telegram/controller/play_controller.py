import random

from telebot.types import Message

from vasiniyo_chat_bot.module.play.dto import Winner
from vasiniyo_chat_bot.module.play.play_service import PlayService
from vasiniyo_chat_bot.telegram.renderer.play_renderer import PlayRenderer


class PlayController:
    def __init__(self, play_service: PlayService, play_renderer: PlayRenderer):
        self.play_service = play_service
        self.play_renderer = play_renderer

    def handle_play(self, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        play_status = self.play_service.get_daily_score(chat_id, user_id)
        self.play_renderer.send_play_result(play_status, chat_id, message.id)

    def handle_players(self, message: Message):
        chat_id = message.chat.id
        category = self.play_service.get_current_playable_category(chat_id)
        leaderboard = self.play_service.get_players(category, chat_id)
        self.play_renderer.send_players(leaderboard, chat_id, message.id)

    def handle_winner(self, message: Message):
        chat_id = message.chat.id
        category = self.play_service.get_current_playable_category(chat_id)
        leaderboard = self.play_service.get_players(category, chat_id)
        winner = self.play_service.handle_winner(leaderboard)
        self.play_renderer.send_winner(winner, category, chat_id, message.id)

    def handle_top_winners(self, message: Message):
        chat_id = message.chat.id
        leaderboard = self.play_service.handle_top_winners(chat_id, limit=10)
        self.play_renderer.send_winners(leaderboard, chat_id, message.id)

    def handle_test_new_winner(self, message: Message):
        chat_id = message.chat.id
        category = self.play_service.get_current_playable_category(chat_id)
        leaderboard = self.play_service.get_players(
            category, chat_id, seed=random.randint(0, 1000)
        )
        winner = Winner(
            winner_id=message.from_user.id,
            value=leaderboard.rows[0].value,
            first_in_day=True,
        )
        self.play_renderer.send_winner(winner, category, chat_id, message.id)

    def handle_test_new_category(self, message: Message):
        chat_id = message.chat.id
        category = self.play_service.get_current_playable_category(chat_id, test=True)
        leaderboard = self.play_service.get_players(
            category,
            chat_id,
            seed=random.randint(0, 1000),
            extra_players=[message.from_user.id],
        )
        self.play_renderer.send_debug_category(
            category, chat_id, message.id, leaderboard
        )

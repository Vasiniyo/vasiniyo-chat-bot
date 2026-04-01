import logging
import random

from vasiniyo_chat_bot.module.likes.dto import Leaderboard
from vasiniyo_chat_bot.module.play.dto import PlayCategory, PlayStatus, Winner
from vasiniyo_chat_bot.module.play.image_service import ImageService
from vasiniyo_chat_bot.telegram.bot_service import (
    BoldTemplate,
    BotService,
    ItalicTemplate,
    UserTemplate,
)


class PlayRenderer:
    _emoji_tiers: list[list[str]] = [
        # fmt: off
        ["😢", "😞", "😔", "😭", "💔", "😰", "😓", "😥", "😣", "😖", "😫", "😩", "😤"],
        ["😐", "😑", "😕", "🙁", "😬", "😶", "😯", "😲", "😧", "😦", "😒"],
        ["😊", "🙂", "😌", "😏", "😀", "😃", "😄", "😺", "😸", "😇", "😎"],
        ["😁", "😆", "🤩", "😍", "😻", "💪", "👍", "✨", "🌟", "💫", "🔥", "🎉", "🎊", ],
        ["🏆", "👑", "💎", "🌈", "🎯", "💯", "🚀", "⚡", "💥", "🔱", "🎭"],
        # fmt: on
    ]

    def __init__(self, bot_service: BotService, image_service: ImageService):
        self.bot_service = bot_service
        self.image_service = image_service

    def send_play_result(self, play_status: PlayStatus, chat_id: int, message_id: int):
        category = play_status.category
        phrase = self._get_phrase_by_value(category, play_status.value)
        category_name = category.name
        units = category.units
        mark = self._get_emoji_for_value(category, play_status.value)
        text_units = [
            "Сегодняшняя категория: ",
            BoldTemplate(category_name),
            f"\nПосмотрим сколько в тебе {units}!\n  {mark}  [",
            BoldTemplate(str(play_status.value)),
            "]: ",
            ItalicTemplate(phrase),
        ]
        self.bot_service.send_message(text_units, chat_id, message_id)

    def send_players(self, leaderboard: Leaderboard, chat_id: int, message_id: int):
        if not leaderboard.rows:
            self.bot_service.send_message(
                "К сожалению, игроков нет...", chat_id, message_id
            )
            return
        self.bot_service.send_leaderboard(
            leaderboard, f"Сегодняшние результаты:", chat_id, message_id
        )

    def send_winner(
        self, winner: Winner, category: PlayCategory, chat_id: int, message_id: int
    ):
        units = category.units
        category_name = category.name
        emoji = self._get_emoji_for_value(category, winner.value, force_top=True)
        text_units = [
            "Победитель в сегодняшней категории (",
            ItalicTemplate(category_name),
            "):\n  ",
            emoji,
            "  ",
            UserTemplate(chat_id, winner.winner_id),
            "\nЦелых [",
            BoldTemplate(str(winner.value)),
            f"] {units}!\nОго! Поздравляю!",
        ]
        if not winner.first_in_day:
            self.bot_service.send_message(text_units, chat_id, message_id)
            return
        try:
            picture = self.image_service.create_picture(
                profile_photo=self.bot_service.get_profile_photo(winner.winner_id)
            )
            self.bot_service.send_photo(picture, chat_id, message_id, text_units)
        except Exception as e:
            logging.exception(e)
            self.bot_service.send_message(text_units, chat_id, message_id)

    def send_winners(self, leaderboard: Leaderboard, chat_id: int, message_id: int):
        if not leaderboard.rows:
            self.bot_service.send_message(
                "Ещё не было сыграно ни одной игры!", chat_id, message_id
            )
            return
        self.bot_service.send_leaderboard(
            leaderboard, "🏆 Топ победителей за всё время:", chat_id, message_id
        )

    def send_debug_category(
        self,
        category: PlayCategory,
        chat_id: int,
        message_id: int,
        leaderboard: Leaderboard,
    ):
        text_units = [
            (
                f"Категория: {category.name}\n"
                f"Способ выявления победителя: {category.win_value.name}\n"
                f"Целевое значение: {category.win_value.value}\n"
                f"Победитель: "
            ),
            UserTemplate(leaderboard.chat_id, leaderboard.rows[0].user_id),
            "\n\nРезультаты всех игроков:\n",
            *[
                item
                for position, row in enumerate(leaderboard.rows)
                for item in [
                    f"{position + 1}. ",
                    UserTemplate(leaderboard.chat_id, row.user_id),
                    f" — {row.value}\n",
                ]
            ],
        ]
        self.bot_service.send_message(text_units, chat_id, message_id=message_id)

    def _get_emoji_for_value(
        self, category: PlayCategory, value: int, force_top: bool = False
    ) -> str:
        if force_top:
            return random.choice(self._emoji_tiers[-1])
        min_v = min(min(category.ranges))
        max_v = max(max(category.ranges))
        value_count = max_v - min_v + 1
        emoji_count = len(self._emoji_tiers)
        step = value_count / emoji_count
        index = max(0, min(emoji_count - 1, int((value - min_v) / step)))
        return random.choice(self._emoji_tiers[index])

    @staticmethod
    def _get_phrase_by_value(category: PlayCategory, value: int) -> str:
        sorted_ranges = sorted(category.thresholds.keys())
        for i in range(len(sorted_ranges)):
            if value <= sorted_ranges[i]:
                return random.choice(category.thresholds[sorted_ranges[i]])
        return random.choice(category.thresholds[0])

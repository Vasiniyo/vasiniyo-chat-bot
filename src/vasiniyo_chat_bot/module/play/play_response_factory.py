import logging
import random

from vasiniyo_chat_bot.module.dto import BoldTemplate
from vasiniyo_chat_bot.module.dto import ItalicTemplate
from vasiniyo_chat_bot.module.dto import Response
from vasiniyo_chat_bot.module.dto import UserTemplate
from vasiniyo_chat_bot.module.like.dto import Leaderboard
from vasiniyo_chat_bot.module.play.dto import PlayCategory
from vasiniyo_chat_bot.module.play.dto import PlayStatus
from vasiniyo_chat_bot.module.play.dto import Winner
from vasiniyo_chat_bot.module.play.image_service import ImageService
from vasiniyo_chat_bot.module.user_service import UserService


class PlayResponseFactory:
    _emoji_tiers: list[list[str]] = [
        ["😢", "😞", "😔", "😭", "💔", "😰", "😓", "😥", "😣", "😖", "😫", "😩", "😤"],
        ["😐", "😑", "😕", "🙁", "😬", "😶", "😯", "😲", "😧", "😦", "😒"],
        ["😊", "🙂", "😌", "😏", "😀", "😃", "😄", "😺", "😸", "😇", "😎"],
        ["😁", "😆", "🤩", "😍", "😻", "💪", "👍", "✨", "🌟", "💫", "🔥", "🎉", "🎊"],
        ["🏆", "👑", "💎", "🌈", "🎯", "💯", "🚀", "⚡", "💥", "🔱", "🎭"],
    ]

    def __init__(self, user_service: UserService, image_service: ImageService):
        self._user_service = user_service
        self._image_service = image_service

    def daily_result(self, play_status: PlayStatus) -> Response:
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
        return Response(text_units=text_units)

    def winner(self, chat_id: int, winner: Winner, category: PlayCategory) -> Response:
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
            return Response(text_units=text_units)
        try:
            picture = self._image_service.create_picture(
                profile_photo=self._user_service.get_photo(winner.winner_id)
            )
            return Response(text_units=text_units, picture=picture)
        except Exception as e:
            logging.exception(e)
            return Response(text_units=text_units)

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
    def players(leaderboard: Leaderboard):
        if not leaderboard.rows:
            text = "К сожалению, игроков нет..."
            return Response(text_units=text)
        text = PlayResponseFactory._get_leaderboard(
            "Сегодняшние результаты:", leaderboard
        )
        return Response(text_units=text)

    @staticmethod
    def leaderboard(leaderboard: Leaderboard):
        if not leaderboard.rows:
            text = "Ещё не было сыграно ни одной игры!"
            return Response(text_units=text)
        text = PlayResponseFactory._get_leaderboard(
            "🏆 Топ победителей за всё время:", leaderboard
        )
        return Response(text_units=text)

    @staticmethod
    def debug_daily_result(category: PlayCategory, leaderboard: Leaderboard):
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
        return Response(text_units=text_units)

    @staticmethod
    def _get_phrase_by_value(category: PlayCategory, value: int) -> str:
        sorted_ranges = sorted(category.thresholds.keys())
        for i in range(len(sorted_ranges)):
            if value <= sorted_ranges[i]:
                return random.choice(category.thresholds[sorted_ranges[i]])
        return random.choice(category.thresholds[0])

    @staticmethod
    def _get_leaderboard(header, leaderboard: Leaderboard) -> list[str | UserTemplate]:
        return [f"{header}\n"] + [
            item
            for position, row in enumerate(leaderboard.rows)
            for item in [
                f"{position + 1}. ",
                UserTemplate(leaderboard.chat_id, row.user_id),
                f" — {row.value}\n",
            ]
        ]

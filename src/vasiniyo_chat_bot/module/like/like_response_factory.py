from vasiniyo_chat_bot.module.dto import Response
from vasiniyo_chat_bot.module.dto import UserTemplate
from vasiniyo_chat_bot.module.like.dto import Leaderboard
from vasiniyo_chat_bot.module.like.dto import Like


class LikeResponseFactory:
    @staticmethod
    def like(like: Like, chat_id: int, to_user_id: int):
        if not like.current_likes:
            text = "🤯 Я не понимаю кому ставить лайк, отправь его ответом на сообщение что ли..."
        else:
            text = [
                f"👍 Лайк засчитан!\nУ ",
                UserTemplate(chat_id, to_user_id),
                f" теперь {like.current_likes} лайков!",
            ]
        return Response(text_units=text)

    @staticmethod
    def leaderboard(leaderboard: Leaderboard) -> Response:
        text = LikeResponseFactory._get_leaderboard("🏆 Топ по лайкам:", leaderboard)
        return Response(text_units=text)

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

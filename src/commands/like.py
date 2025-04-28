from config import bot, phrases
from database.likes import add_like, count_likes
import safely_bot_utils as bot


def handle_like(message):
    if reply_to_message := message.reply_to_message:
        from_user = message.from_user
        to_user = reply_to_message.from_user
        add_like(message.chat.id, from_user.id, to_user.id)
        answer = phrases(
            "like_ok", to_user.first_name, count_likes(message.chat.id, to_user.id)
        )
    else:
        answer = phrases("like_no_ok")
    bot.reply_to(answer)(message)

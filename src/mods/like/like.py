from telebot.types import LinkPreviewOptions

from config import bot, phrases
from database.likes import add_like, count_likes, fetch_top
import safely_bot_utils as bot

from ..register import reg_command

# ========== COMMANDS =========================================================


@reg_command("top_likes", phrases("top_likes_help"))
def handle_top_likes(message):
    bot.reply_top(
        lambda: fetch_top(message.chat.id, 10),
        message.chat.id,
        phrases("top_likes_header"),
    )(message)


@reg_command("like", phrases("like_help"))
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

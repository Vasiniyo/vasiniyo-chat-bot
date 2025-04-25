from telebot.types import LinkPreviewOptions

from config import phrases
from database.likes import fetch_top
import safely_bot_utils as bot


def handle_top(message):
    def get_user_name(chat_id, user_id):
        user = bot.get_chat_member(chat_id, user_id).user
        return bot.to_link_user(user)

    top_message = "\n".join(
        f"{position + 1}. {get_user_name(message.chat.id, user_id)} — {count}"
        for position, (user_id, count) in enumerate(fetch_top(message.chat.id, 10))
    )
    bot.reply_with_user_links(f"{phrases('top_header')}\n{top_message}")(message)

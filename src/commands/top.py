from telebot.types import LinkPreviewOptions

from config import bot
from database.likes import fetch_top


def handle_top(message):
    def get_user_name(chat_id, user_id):
        user = bot.get_chat_member(chat_id, user_id).user
        if not (user.username is None):
            return f"{user.first_name} ([{user.username}](t.me/{user.username}))"
        return f"[{user.first_name}](tg://user?id={user.id})"

    top_message = "\n".join(
        f"{position + 1}. {get_user_name(message.chat.id, user_id)} — {count}"
        for position, (user_id, count) in enumerate(fetch_top(message.chat.id, 10))
    )
    bot.reply_to(
        message,
        f"🏆 Топ по лайкам:\n{top_message}",
        parse_mode="Markdown",
        disable_notification=True,
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )

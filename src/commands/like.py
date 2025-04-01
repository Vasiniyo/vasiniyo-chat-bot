from config import bot
from database.likes import add_like, count_likes


def handle_like(message):
    if reply_to_message := message.reply_to_message:
        from_user = message.from_user
        to_user = reply_to_message.from_user
        add_like(message.chat.id, from_user.id, to_user.id)
        bot.reply_to(
            message,
            f"👍 Лайк засчитан!\nУ {to_user.first_name} теперь {count_likes(message.chat.id, to_user.id)} лайков!",
        )
    else:
        bot.reply_to(
            message,
            "🤯 Я не понимаю кому ставить лайк, отправь его ответом на сообщение что ли...",
        )

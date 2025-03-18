import logging
import random

from config import bot, templates
from constansts import ANDRUXA_TANENBAUM_PHRASES, IS_TANENBAUM, MESSAGE_MAX_LEN
from likes import add_like, count_likes, fetch_top

logger = logging.getLogger(__name__)


def get_user_name(chat_id, user_id):
    user = bot.get_chat_member(chat_id, user_id).user
    return f"{user.first_name} (@{user.username})"


def to_long_message(message):
    bot.reply_to(message, "Многа букав, не осилил!")


@bot.message_handler(commands=["top"])
def handle_top(message):
    top_message = "\n".join(
        f"{position + 1}. {get_user_name(message.chat.id, user_id)} — {count}"
        for position, (user_id, count) in enumerate(fetch_top(message.chat.id, 10))
    )
    bot.reply_to(message, f"🏆 Топ по лайкам:\n{top_message}")


@bot.message_handler(commands=["like"])
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


@bot.message_handler(func=lambda message: True)
def reply_text(message):
    user_message = message.text.lower()

    if len(user_message) > MAX_MESSAGE_LEN:
        to_long_message(message)
    elif reply := templates["text_to_text"].get(user_message):
        reply = __get_tanenbaum_phrase(user_message)
        bot.reply_to(message, reply)
    elif sticker_file_id := templates["text_to_sticker"].get(user_message):
        bot.send_sticker(
            message.chat.id, sticker_file_id, reply_to_message_id=message.message_id
        )


@bot.message_handler(content_types=["sticker"])
def reply_sticker(message):
    if sticker_file_id := templates["sticker_to_sticker"].get(message.sticker.file_id):
        bot.send_sticker(
            message.chat.id, sticker_file_id, reply_to_message_id=message.message_id
        )


def __get_tanenbaum_phrase(message):
    if message == IS_TANENBAUM:
        return random.choice(ANDRUXA_TANENBAUM_PHRASES)
    return message


if __name__ == "__main__":
    logger.info("Bot started")
    bot.polling()

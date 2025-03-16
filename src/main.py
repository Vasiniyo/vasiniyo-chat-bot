import logging

from config import bot, templates

logger = logging.getLogger(__name__)


@bot.message_handler(func=lambda message: True)
def reply_text(message):
    if reply := templates["text_to_text"].get(message.text):
        bot.reply_to(message, reply)
    elif sticker_file_id := templates["text_to_sticker"].get(message.text):
        bot.send_sticker(
            message.chat.id, sticker_file_id, reply_to_message_id=message.message_id
        )


@bot.message_handler(content_types=["sticker"])
def reply_sticker(message):
    if sticker_file_id := templates["sticker_to_sticker"].get(message.sticker.file_id):
        bot.send_sticker(
            message.chat.id, sticker_file_id, reply_to_message_id=message.message_id
        )


if __name__ == "__main__":
    logger.info("Bot started")
    bot.polling()

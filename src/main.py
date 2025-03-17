import logging
from config import setup_logging, init_bot, load_stickers

def register_handlers(bot, templates):
    @bot.message_handler(func=lambda message: True)
    def reply_text(message):
        if reply := templates["text_to_text"].get(message.text):
            bot.reply_to(message, reply)
        elif sticker_file_id := templates["text_to_sticker"].get(message.text):
            bot.send_sticker(
                message.chat.id,
                sticker_file_id,
                reply_to_message_id=message.message_id
            )

    @bot.message_handler(content_types=["sticker"])
    def reply_sticker(message):
        if sticker_file_id := templates["sticker_to_sticker"].get(message.sticker.file_id):
            bot.send_sticker(
                message.chat.id,
                sticker_file_id,
                reply_to_message_id=message.message_id
            )

def main():
    logger = setup_logging()
    bot = init_bot()
    templates = load_stickers(bot)
    register_handlers(bot, templates)
    logger.info("Bot started")
    bot.polling()

if __name__ == "__main__":
    main()

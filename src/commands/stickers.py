from config import bot, templates


def handle_stickers(message):
    if sticker_file_id := templates["sticker_to_sticker"].get(message.sticker.file_id):
        bot.send_sticker(
            message.chat.id, sticker_file_id, reply_to_message_id=message.message_id
        )

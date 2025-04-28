import asyncio
import datetime
import logging
import threading

from telebot.types import LinkPreviewOptions

from config import bot
from logger import logger


def start_loop():
    asyncio.set_event_loop(loop)
    loop.run_forever()


def do_action(func):
    def wrapper(*args, **kwargs):
        try:
            return logger(func)(*args, **kwargs)
        except Exception as e:
            logging.exception(e)
            return None

    return wrapper


@logger
def delete_message_later(message, delay=10):
    async def delete_message():
        await asyncio.sleep(delay)
        do_action(bot.delete_message)(message.chat.id, message.message_id)

    asyncio.run_coroutine_threadsafe(delete_message(), loop)


@logger
def edit_message_text_later(text, **kwargs):
    async def edit_message(message, delay):
        await asyncio.sleep(delay)
        return edit_message_text(text, **kwargs)(message)

    return lambda m, delay=5: asyncio.run_coroutine_threadsafe(
        edit_message(m, delay), loop
    )


edit_message_text = lambda text, **kwargs: lambda m: (
    do_action(bot.edit_message_text)(text, m.chat.id, m.message_id, **kwargs)
)

edit_message_reply_markup = lambda m: (
    bot.edit_message_reply_markup(m.chat.id, m.message_id, reply_markup=None)
)

reply_to = lambda t, **kwargs: lambda m: do_action(bot.reply_to)(m, t, **kwargs)

reply_with_user_links = lambda text: reply_to(
    text,
    parse_mode="Markdown",
    disable_notification=True,
    link_preview_options=LinkPreviewOptions(is_disabled=True),
)


def to_link_user(user):
    if not (user.username is None):
        return f"{user.first_name} ([{user.username}](t.me/{user.username}))"
    return f"{user.first_name}"


def daily_hash(user_id):
    """
    https://gist.github.com/badboy/6267743
    """
    key = user_id + datetime.date.today().toordinal()
    key = (key ^ 61) ^ (key >> 16)
    key = key + (key << 3)
    key = key ^ (key >> 4)
    key = key * 0x27D4EB2D
    key = key ^ (key >> 15)
    return key


get_chat_member = lambda chat_id, user_id: (
    do_action(bot.get_chat_member)(chat_id, user_id)
)

answer_callback_query = lambda t: lambda c: (
    do_action(bot.answer_callback_query)(c.id, text=t)
)

get_chat_administrators = lambda chat_id: (
    do_action(bot.get_chat_administrators)(chat_id)
)

set_chat_administrator_custom_title = lambda chat_id, user_id, title: (
    do_action(bot.set_chat_administrator_custom_title)(chat_id, user_id, title)
)

promote_chat_member = lambda chat_id, user_id, **kwargs: (
    do_action(bot.promote_chat_member)(chat_id, user_id, **kwargs)
)

send_dice = lambda m: (
    do_action(bot.send_dice)(m.chat.id, reply_to_message_id=m.message_id, emoji="🎲")
)

send_sticker = lambda file_id: lambda m: (
    do_action(bot.send_sticker)(m.chat.id, file_id, reply_to_message_id=m.message_id)
)

answer_inline_query = lambda cmds: lambda query: (
    do_action(bot.answer_inline_query)(query.id, cmds)
)

get_me = do_action(bot.get_me)

loop = asyncio.new_event_loop()
threading.Thread(target=start_loop, daemon=True).start()

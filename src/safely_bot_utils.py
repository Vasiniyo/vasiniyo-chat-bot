import asyncio
import datetime
import logging
import random
import threading

from telebot.types import LinkPreviewOptions

from config import bot, phrases
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

reply_with_user_links = lambda text, mode="Markdown": reply_to(
    text,
    parse_mode=mode,
    disable_notification=True,
    link_preview_options=LinkPreviewOptions(is_disabled=True),
)


# NOTE probably should leave only one of makrdown senders
def escape_markdown_v2(text) -> str:
    """Escape special characters for MarkdownV2."""
    if text is None:
        return ""
    text = str(text)
    # fmt: off
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    # fmt: on
    for char in special_chars:
        text = text.replace(char, f"\\{char}")
    return text


def to_link_user(user):
    if user is None:
        return phrases("unknown_user")
    if not (user.username is None):
        return f"{user.first_name} ([{user.username}](t.me/{user.username}))"
    return f"{user.first_name}"


def to_link_user_v2(user):
    """MarkdownV2 compatible user link"""
    if user is None:
        return escape_markdown_v2(phrases("unknown_user"))

    first_name_escaped = escape_markdown_v2(user.first_name)

    if user.username:
        username_escaped = escape_markdown_v2(user.username)
        url = f"https://t\\.me/{username_escaped}"
        return f"{first_name_escaped} \\([{username_escaped}]({url})\\)"

    return first_name_escaped


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


def get_user_name(chat_id, user_id):
    member = get_chat_member(chat_id, user_id)
    user = member.user if member is not None else None
    return to_link_user(user)


def reply_top(fetch, chat_id, header):
    top_message = "\n".join(
        f"{position + 1}. {get_user_name(chat_id, user_id)} — {count}"
        for position, (user_id, count) in enumerate(fetch())
    )
    return reply_with_user_links(f"{header}\n{top_message}") or (lambda: None)


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

dices = {
    "⚽": {"weight": 25, "win_values": (3, 4, 5)},
    "🏀": {"weight": 25, "win_values": (4, 5)},
    "🎯": {"weight": 54, "win_values": (6,)},
    "🎳": {"weight": 54, "win_values": (6,)},
    "🎰": {"weight": 112, "win_values": (1, 22, 43, 64)},
}

dice_keys = list(dices.keys())
dice_weights = [dices[item]["weight"] for item in dice_keys]

send_random_dice = lambda m: (
    do_action(bot.send_dice)(
        m.chat.id,
        reply_to_message_id=m.message_id,
        emoji=random.choices(dice_keys, weights=dice_weights)[0],
    )
)

send_sticker = lambda file_id: lambda m: (
    do_action(bot.send_sticker)(m.chat.id, file_id, reply_to_message_id=m.message_id)
)

answer_inline_query = lambda cmds: lambda query: (
    do_action(bot.answer_inline_query)(query.id, cmds)
)

get_file = lambda file_id: (do_action(bot.get_file)(file_id))

download_file = lambda file_path: (do_action(bot.download_file)(file_path))

send_photo_with_user_links = lambda photo, caption: lambda message: (
    do_action(bot.send_photo)(
        message.chat.id,
        reply_to_message_id=message.message_id,
        photo=photo,
        caption=caption,
        parse_mode="Markdown",
        disable_notification=True,
    )
)


def get_user_profile_photo_file_info(user_id):
    photo = do_action(bot.get_user_profile_photos)(user_id, limit=1)
    return get_file(photo.photos[0][-1].file_id) if photo.photos else None


def download_profile_photo(user_id):
    file_info = get_user_profile_photo_file_info(user_id)
    return download_file(file_info.file_path) if file_info else None


get_me = do_action(bot.get_me)

loop = asyncio.new_event_loop()
threading.Thread(target=start_loop, daemon=True).start()

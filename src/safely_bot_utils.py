import asyncio
from concurrent.futures import Future
import datetime
from locale import locale
import random
import threading
from typing import Callable, Iterable, Optional, ParamSpec, TypeVar

from telebot.types import (
    CallbackQuery,
    ChatMember,
    File,
    InlineQuery,
    LinkPreviewOptions,
    Message,
    User,
)

from config import bot, config
from logger import get_json_logger, logger

P = ParamSpec("P")
R = TypeVar("R")


def start_loop():
    asyncio.set_event_loop(loop)
    loop.run_forever()


def do_action(func: Callable[P, R]) -> Callable[P, R]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Optional[R]:
        try:
            return logger(func)(*args, **kwargs)
        except Exception as e:
            get_json_logger().exception(e)
            return None

    return wrapper


@logger
def delete_message_later(message: Message, delay=10) -> None:
    async def delete_message() -> None:
        await asyncio.sleep(delay)
        do_action(bot.delete_message)(message.chat.id, message.message_id)

    asyncio.run_coroutine_threadsafe(delete_message(), loop)


@logger
def edit_message_text_later(
    text: str, delay: int = 5, should_edit: Callable[[], bool] = lambda: True, **kwargs
) -> Callable[[Message], Future]:
    async def edit_message(message: Message):
        await asyncio.sleep(delay)
        if should_edit():
            return edit_message_text(text, **kwargs)(message)
        return None

    return lambda message: (
        asyncio.run_coroutine_threadsafe(edit_message(message), loop)
    )


def edit_message_text(text: str, **kwargs) -> Callable[[Message], None]:
    return lambda message: (
        do_action(bot.edit_message_text)(
            text, message.chat.id, message.message_id, **kwargs
        )
    )


def edit_message_reply_markup(message: Message) -> Callable[[Message], None]:
    return bot.edit_message_reply_markup(
        message.chat.id, message.message_id, reply_markup=None
    )


def reply_to(text: str, **kwargs) -> Callable[[Message], None]:
    return lambda message: do_action(bot.reply_to)(message, text, **kwargs)


def reply_with_user_links(text: str, mode="Markdown") -> Callable[[Message], None]:
    return reply_to(
        text,
        parse_mode=mode,
        disable_notification=True,
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


# NOTE probably should leave only one of markdown senders
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


def to_link_user(user: User) -> str:
    if user is None:
        return phrases("unknown_user")
    if not (user.username is None):
        return f"{user.first_name} ([{user.username}](t.me/{user.username}))"
    return f"{user.first_name}"


def to_link_user_v2(user: User) -> str:
    """MarkdownV2 compatible user link"""
    if user is None:
        return escape_markdown_v2(phrases("unknown_user"))

    first_name_escaped = escape_markdown_v2(user.first_name)

    if user.username:
        username_escaped = escape_markdown_v2(user.username)
        url = f"https://t\\.me/{username_escaped}"
        return f"{first_name_escaped} \\([{username_escaped}]({url})\\)"

    return first_name_escaped


def daily_hash(salt: int) -> int:
    """
    https://gist.github.com/badboy/6267743
    """
    key = salt + datetime.date.today().toordinal()
    key = (key ^ 61) ^ (key >> 16)
    key = key + (key << 3)
    key = key ^ (key >> 4)
    key = key * 0x27D4EB2D
    key = key ^ (key >> 15)
    return key


def get_user_name(chat_id: int, user_id: int) -> Optional[str]:
    member = get_chat_member(chat_id, user_id)
    user = member.user if member is not None else None
    return to_link_user(user)


def reply_top(
    fetch: Callable[[], Iterable[tuple[int, int]]], chat_id: int, header: str
) -> Callable[[Message], None]:
    top_message = "\n".join(
        f"{position + 1}. {get_user_name(chat_id, user_id)} — {count}"
        for position, (user_id, count) in enumerate(fetch())
    )
    return reply_with_user_links(f"{header}\n{top_message}") or (lambda: None)


def get_chat_member(chat_id, user_id) -> ChatMember:
    return do_action(bot.get_chat_member)(chat_id, user_id)


def answer_callback_query(text: str) -> Callable[[CallbackQuery], None]:
    return lambda call: (do_action(bot.answer_callback_query)(call.id, text=text))


def get_chat_administrators(chat_id: int) -> list[ChatMember]:
    return do_action(bot.get_chat_administrators)(chat_id)


def set_chat_administrator_custom_title(chat_id: int, user_id: int, title: str) -> None:
    return do_action(bot.set_chat_administrator_custom_title)(chat_id, user_id, title)


def promote_chat_member(chat_id: int, user_id: int, **kwargs) -> None:
    return do_action(bot.promote_chat_member)(chat_id, user_id, **kwargs)


def send_dice(message: Message) -> Message:
    return do_action(bot.send_dice)(
        message.chat.id, reply_to_message_id=message.message_id, emoji="🎲"
    )


DICES = {
    "⚽": {"weight": 25, "win_values": (3, 4, 5)},
    "🏀": {"weight": 25, "win_values": (4, 5)},
    "🎯": {"weight": 54, "win_values": (6,)},
    "🎳": {"weight": 54, "win_values": (6,)},
    "🎰": {"weight": 112, "win_values": (1, 22, 43, 64)},
}

_dice_keys = list(DICES.keys())
_dice_weights = [DICES[item]["weight"] for item in _dice_keys]


def send_random_dice(message: Message) -> Message:
    return do_action(bot.send_dice)(
        message.chat.id,
        reply_to_message_id=message.message_id,
        emoji=random.choices(_dice_keys, weights=_dice_weights)[0],
    )


def send_sticker(file_id: int) -> Callable[[Message], Message]:
    return lambda message: do_action(bot.send_sticker)(
        message.chat.id, file_id, reply_to_message_id=message.id
    )


def answer_inline_query(commands: list) -> Callable[[InlineQuery], None]:
    return lambda query: do_action(bot.answer_inline_query)(query.id, commands)


def get_file(file_id: int) -> File:
    return do_action(bot.get_file)(file_id)


def download_file(file_path: str) -> bytes:
    return do_action(bot.download_file)(file_path)


def send_photo_with_user_links(
    photo: str, caption: Optional[str], parse_mode: str = "Markdown"
) -> Callable[[Message], Message]:
    return lambda message: (
        do_action(bot.send_photo)(
            message.chat.id,
            reply_to_message_id=message.message_id,
            photo=photo,
            caption=caption,
            parse_mode=parse_mode,
            disable_notification=True,
        )
    )


def get_user_profile_photo_file_info(user_id: int) -> Optional[File]:
    photo = do_action(bot.get_user_profile_photos)(user_id, limit=1)
    return get_file(photo.photos[0][-1].file_id) if photo.photos else None


def download_profile_photo(user_id: int) -> Optional[bytes]:
    file_info = get_user_profile_photo_file_info(user_id)
    return download_file(file_info.file_path) if file_info else None


get_me = do_action(bot.get_me)


def phrases(k: str, *args) -> str:
    if config.language not in locale:
        config.language = "ru"
    if k in locale[config.language]:
        return locale[config.language][k].format(*args)
    return "Мне нечего тебе сказать..."


loop = asyncio.new_event_loop()
threading.Thread(target=start_loop, daemon=True).start()

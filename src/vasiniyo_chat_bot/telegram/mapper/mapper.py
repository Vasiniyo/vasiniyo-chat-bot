from telebot.types import CallbackQuery
from telebot.types import Message

from vasiniyo_chat_bot.module.anime.anime_controller import AnimeCallbackContext
from vasiniyo_chat_bot.module.anime.anime_payload_factory import AnimePayloadFactory
from vasiniyo_chat_bot.module.captcha.captcha_controller import CaptchaCallbackContext
from vasiniyo_chat_bot.module.captcha.captcha_payload_factory import (
    CaptchaPayloadFactory,
)
from vasiniyo_chat_bot.module.dto import MessageContext
from vasiniyo_chat_bot.module.titles.dto import TitlesCallbackContext
from vasiniyo_chat_bot.module.titles.titles_payload_factory import TitlesPayloadFactory


def message_to_context(message: Message) -> MessageContext:
    reply_to_message = message.reply_to_message
    return MessageContext(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        message_id=message.id,
        inline_message_id=None,
        prev=(
            MessageContext(
                user_id=reply_to_message.from_user.id,
                chat_id=reply_to_message.chat.id,
                message_id=reply_to_message.id,
                inline_message_id=None,
                prev=None,
                file_id=(
                    reply_to_message.sticker.file_id
                    if reply_to_message.sticker
                    else None
                ),
                text=reply_to_message.text,
            )
            if reply_to_message
            else None
        ),
        file_id=message.sticker.file_id if message.sticker else None,
        text=message.text,
    )


def call_to_titles_context(call: CallbackQuery) -> TitlesCallbackContext:
    return TitlesCallbackContext(
        user_id=call.from_user.id,
        chat_id=call.message.chat.id,
        message_id=call.message.id,
        inline_message_id=None,
        callback_id=call.id,
        payload=TitlesPayloadFactory.get_payload(call.data),
    )


def call_to_captcha_context(call: CallbackQuery) -> CaptchaCallbackContext:
    return CaptchaCallbackContext(
        user_id=call.from_user.id,
        chat_id=call.message.chat.id,
        message_id=call.message.id,
        inline_message_id=None,
        callback_id=call.id,
        payload=CaptchaPayloadFactory.get_payload(call.data),
    )


def call_to_anime_context(call: CallbackQuery) -> AnimeCallbackContext:
    return AnimeCallbackContext(
        user_id=call.from_user.id,
        chat_id=None,
        message_id=None,
        inline_message_id=call.inline_message_id,
        callback_id=call.id,
        payload=AnimePayloadFactory.get_payload(call.data),
    )

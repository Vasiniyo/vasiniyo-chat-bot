from telebot.types import CallbackQuery
from telebot.types import Message

from vasiniyo_chat_bot.module.dto import CallbackContext
from vasiniyo_chat_bot.module.dto import InlineCallbackContext
from vasiniyo_chat_bot.module.dto import MessageContext
from vasiniyo_chat_bot.module.payload_factory import PayloadFactory


def message_to_context(message: Message) -> MessageContext | None:
    reply_to_message = message.reply_to_message
    if message.from_user is None:
        return None
    return MessageContext(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        message_id=message.id,
        prev=(
            MessageContext(
                user_id=reply_to_message.from_user.id,
                chat_id=reply_to_message.chat.id,
                message_id=reply_to_message.id,
                prev=None,
                file_id=(
                    reply_to_message.sticker.file_id
                    if reply_to_message.sticker
                    else None
                ),
                text=reply_to_message.text,
            )
            if reply_to_message and reply_to_message.from_user
            else None
        ),
        file_id=message.sticker.file_id if message.sticker else None,
        text=message.text,
    )


def call_to_callback_context(call: CallbackQuery) -> CallbackContext | None:
    message = call.message
    if not message:
        return None
    return CallbackContext(
        user_id=call.from_user.id,
        chat_id=message.chat.id,
        message_id=message.id,
        callback_id=call.id,
        payload=PayloadFactory.load(call.data),
    )


def call_to_inline_callback_context(
    call: CallbackQuery,
) -> InlineCallbackContext | None:
    message_id = call.inline_message_id
    chat_id = call.chat_instance
    if not message_id or not chat_id:
        return None
    return InlineCallbackContext(
        callback_id=call.id,
        user_id=call.from_user.id,
        chat_id=int(chat_id),
        inline_message_id=message_id,
        payload=PayloadFactory.load(call.data),
    )

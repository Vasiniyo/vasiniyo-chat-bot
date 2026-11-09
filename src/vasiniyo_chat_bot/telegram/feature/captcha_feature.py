from typing import Callable

from injector import inject
from telebot.types import CallbackQuery
from telebot.types import Message

from vasiniyo_chat_bot.config.dto import BotSettings
from vasiniyo_chat_bot.module.captcha.captcha_controller import CaptchaController
from vasiniyo_chat_bot.module.dto import Action
from vasiniyo_chat_bot.module.dto import MessageContext
from vasiniyo_chat_bot.module.payload_factory import PayloadFactory
from vasiniyo_chat_bot.module.user_service import UserService
from vasiniyo_chat_bot.telegram.bot_service import BotService
from vasiniyo_chat_bot.telegram.feature.feature import Feature
from vasiniyo_chat_bot.telegram.filter import Filter
from vasiniyo_chat_bot.telegram.handler.left_chat_member_handler import (
    LeftChatMemberHandler,
)
from vasiniyo_chat_bot.telegram.handler.message_handler import MessageHandler
from vasiniyo_chat_bot.telegram.handler.new_member_handler import NewMemberHandler
from vasiniyo_chat_bot.telegram.handler.query_handler import QueryHandler
from vasiniyo_chat_bot.telegram.mapper.mapper import call_to_callback_context
from vasiniyo_chat_bot.telegram.mapper.mapper import message_to_context


@inject
class CaptchaFeature(Feature):
    _valid_payload_actions = {Action.CAPTCHA_UPDATE}

    def __init__(
        self,
        settings: BotSettings,
        bot_service: BotService,
        controller: CaptchaController,
        user_service: UserService,
    ):
        self._controller = controller
        self._user_service = user_service
        message_handlers = self._message_handlers(settings.allowed_chats)
        callback_handlers = self._callback_handlers(settings.allowed_chats)
        super().__init__(
            settings,
            bot_service,
            message_handlers=message_handlers,
            callback_handlers=callback_handlers,
        )

    def _message_handlers(self, allowed_chats: list[str]) -> list[MessageHandler]:
        def _is_captcha_user(message: Message):
            ctx = message_to_context(message)
            return self._controller.is_captcha_user(ctx) if ctx else False

        return [
            NewMemberHandler(
                allowed_chats,
                self._invalidate_user_cache(self._controller.handle_new_user),
            ),
            LeftChatMemberHandler(allowed_chats, self._invalidate_user_cache()),
            MessageHandler(
                allowed_chats,
                self._controller.handle_verify_captcha,
                Filter(_is_captcha_user),
                content_types=[
                    # fmt: off
                    "animation", "audio", "contact", "dice",
                    "document", "location", "photo", "text",
                    "sticker", "video", "video_note", "voice"
                    # fmt: on
                ],
            ),
        ]

    def _callback_handlers(self, allowed_chats: list[str]) -> list[QueryHandler]:
        def _is_captcha_user(call: CallbackQuery):
            ctx = call_to_callback_context(call)
            return self._controller.is_captcha_user(ctx) if ctx else False

        def has_action(call: CallbackQuery):
            return PayloadFactory.has_action(call.data, self._valid_payload_actions)

        return [
            QueryHandler(
                allowed_chats,
                self._controller.handle_captcha_button_press,
                Filter(_is_captcha_user) and Filter(has_action),
            )
        ]

    def _invalidate_user_cache(
        self, func: Callable[[MessageContext], None] = lambda _: None
    ):
        def handler(ctx: MessageContext):
            self._user_service.invalidate_cache(ctx.chat_id, ctx.user_id)
            func(ctx)

        return handler

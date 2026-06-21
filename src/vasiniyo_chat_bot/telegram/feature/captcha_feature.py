from typing import Callable

from vasiniyo_chat_bot.module.captcha.captcha_controller import CaptchaController
from vasiniyo_chat_bot.module.captcha.captcha_payload_factory import (
    CaptchaPayloadFactory,
)
from vasiniyo_chat_bot.module.dto import UserContext
from vasiniyo_chat_bot.module.user_service import UserService
from vasiniyo_chat_bot.telegram.feature.feature import Feature
from vasiniyo_chat_bot.telegram.filter import Filter
from vasiniyo_chat_bot.telegram.handler.captcha_query_handler import CaptchaQueryHandler
from vasiniyo_chat_bot.telegram.handler.left_chat_member_handler import (
    LeftChatMemberHandler,
)
from vasiniyo_chat_bot.telegram.handler.message_handler import MessageHandler
from vasiniyo_chat_bot.telegram.handler.new_member_handler import NewMemberHandler
from vasiniyo_chat_bot.telegram.handler.query_handler import QueryHandler
from vasiniyo_chat_bot.telegram.mapper.mapper import call_to_titles_context
from vasiniyo_chat_bot.telegram.mapper.mapper import message_to_context


class CaptchaFeature(Feature):
    def __init__(
        self,
        bot_username: str,
        allowed_chats: list[str],
        controller: CaptchaController | None,
        user_service: UserService,
    ):
        self._controller = controller
        self._user_service = user_service
        message_handlers = self._message_handlers(allowed_chats, controller)
        callback_handlers = self._callback_handlers(allowed_chats)
        super().__init__(
            bot_username,
            allowed_chats,
            message_handlers=message_handlers,
            callback_handlers=callback_handlers,
        )

    def _message_handlers(
        self, allowed_chats: list[str], controller: CaptchaController
    ) -> list[MessageHandler]:
        return [
            NewMemberHandler(
                allowed_chats,
                self._invalidate_user_cache(
                    controller.handle_new_user if controller else lambda _: None
                ),
            ),
            LeftChatMemberHandler(allowed_chats, self._invalidate_user_cache()),
            MessageHandler(
                allowed_chats,
                controller.handle_verify_captcha,
                Filter(
                    lambda message: controller.is_captcha_user(
                        message_to_context(message)
                    )
                ),
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
        is_captcha_user = Filter(
            lambda call: self._controller.is_captcha_user(call_to_titles_context(call))
        )
        has_captcha_payload = Filter(
            lambda call: CaptchaPayloadFactory.has_captcha_payload(call.data)
        )
        return [
            CaptchaQueryHandler(
                allowed_chats,
                self._controller.handle_captcha_button_press,
                is_captcha_user and has_captcha_payload,
            )
        ]

    def _invalidate_user_cache(
        self, func: Callable[[UserContext], None] = lambda _: None
    ):
        def handler(ctx: UserContext):
            self._user_service.invalidate_cache(ctx.chat_id, ctx.user_id)
            func(ctx)

        return handler

from dataclasses import dataclass
from dataclasses import fields
from dataclasses import replace
import logging

from injector import inject

from vasiniyo_chat_bot.event_queue import EVENTS
from vasiniyo_chat_bot.event_queue import add_task
from vasiniyo_chat_bot.event_queue import cancel_task
from vasiniyo_chat_bot.module.captcha.captcha_response_factory import (
    CaptchaResponseFactory,
)
from vasiniyo_chat_bot.module.captcha.captcha_service import CaptchaService
from vasiniyo_chat_bot.module.dto import CallbackContext
from vasiniyo_chat_bot.module.dto import MessageContext
from vasiniyo_chat_bot.module.dto import UserContext
from vasiniyo_chat_bot.module.renderer import Renderer
from vasiniyo_chat_bot.module.user_service import UserService

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _CaptchaSession:
    task_id: str
    message_id: int


class _CaptchaQueue:
    def __init__(self) -> None:
        self._data: dict[tuple, _CaptchaSession] = {}

    @staticmethod
    def _key(ctx: UserContext) -> tuple:
        return tuple(getattr(ctx, field.name) for field in fields(UserContext))

    def __setitem__(self, ctx: UserContext, value: _CaptchaSession) -> None:
        self._data[self._key(ctx)] = value

    def __getitem__(self, ctx: UserContext) -> _CaptchaSession:
        return self._data[self._key(ctx)]

    def get(self, ctx: UserContext, default=None):
        return self._data.get(self._key(ctx), default)

    def pop(self, ctx: UserContext, default=None) -> _CaptchaSession:
        return self._data.pop(self._key(ctx), default)

    def __contains__(self, ctx: UserContext) -> bool:
        return self._key(ctx) in self._data


@inject
class CaptchaController:
    def __init__(
        self,
        user_service: UserService,
        captcha_service: CaptchaService,
        response_factory: CaptchaResponseFactory,
        renderer: Renderer,
    ) -> None:
        self._user_service = user_service
        self._captcha_service = captcha_service
        self._response_factory = response_factory
        self._renderer = renderer
        self._captcha_queue = _CaptchaQueue()

    def handle_new_user(self, ctx: MessageContext):
        user = self._captcha_service.generate_captcha(ctx.chat_id, ctx.user_id)
        freq = self._captcha_service.captcha_properties().validate.update_freq
        timestamps = list(range(freq, user.time_left + 1, freq))
        response = self._response_factory.captcha(user)
        captcha_message_id = self._renderer.send(response, ctx)
        if not captcha_message_id:
            _logger.warning(
                "captcha_new_user",
                extra={
                    "details": "failed to send captcha",
                    "captcha_message_id": captcha_message_id,
                },
            )
            return
        _logger.info(
            "captcha_new_user",
            extra={
                "chat_id": user.chat_id,
                "user_id": user.user_id,
                "attempts": user.failed_attempts,
                "time_seconds": user.time_left,
                "answer": user.answer,
            },
        )
        task_id = add_task(
            timestamps=timestamps,
            default=lambda: self.update_captcha_message(ctx),
            conditional_funcs={
                "on_success": lambda: self.handle_captcha_failure(ctx, "Время вышло"),
                "on_cancel": lambda: self.handle_captcha_failure(ctx, "Капча отменена"),
            },
        )
        session = _CaptchaSession(task_id, captcha_message_id)
        self._captcha_queue[ctx] = session

    def handle_verify_captcha(self, ctx: MessageContext):
        _logger.info(f"<ctx>: {ctx}")
        self._renderer.delete(ctx)
        if self._captcha_service.validate_captcha(ctx.chat_id, ctx.user_id, ctx.text):
            self.handle_captcha_success(ctx)
            return
        user = self._captcha_service.increase_failed_attempts(ctx.chat_id, ctx.user_id)
        if not user:
            return
        if self._captcha_service.attempts_remained(user):
            self.update_captcha_message(ctx)
        else:
            self.handle_captcha_failure(ctx, "Max attempts used")

    def handle_captcha_button_press(self, ctx: CallbackContext):
        payload = ctx.payload
        if not payload or ctx.user_id != payload.user_id:
            response = self._response_factory.no_access()
            self._renderer.alert(response, ctx)
            return
        user = self._captcha_service.regenerate_captcha(ctx.chat_id, ctx.user_id)
        session = self._captcha_queue.get(ctx)
        if session:
            response = self._response_factory.captcha(user)
            self._renderer.edit(response, replace(ctx, message_id=session.message_id))

    def handle_captcha_success(self, ctx: MessageContext):
        session = self._captcha_queue.pop(ctx, None)
        if session:
            cancel_task(session.task_id, silently=True)
            response = self._response_factory.passed_captcha()
            self._captcha_service.remove_user(ctx.chat_id, ctx.user_id)
            self._renderer.delete(replace(ctx, message_id=session.message_id))
            self._renderer.send(response, ctx)

    def handle_captcha_failure(self, ctx: MessageContext, reason: str):
        session = self._captcha_queue.get(ctx)
        if session:
            self._captcha_queue.pop(ctx, None)
            self._captcha_service.remove_user(ctx.chat_id, ctx.user_id)
            response = self._response_factory.failed_captcha(reason)
            self._renderer.edit_caption(
                response, replace(ctx, message_id=session.message_id)
            )
        self._user_service.ban(ctx)

    def update_captcha_message(self, ctx: MessageContext):
        timer = self._captcha_service.captcha_properties().validate.timer
        session = self._captcha_queue.get(ctx)
        if session:
            event = EVENTS.get(session.task_id, {})
            event_offset = event.get("offset", timer)
            event_time_left = timer - event_offset
            user = self._captcha_service.update_captcha_time_left(
                ctx.chat_id, ctx.user_id, event_time_left
            )
            response = self._response_factory.description(user)
            self._renderer.edit_caption(
                response, replace(ctx, message_id=session.message_id)
            )

    def is_captcha_user(self, ctx: UserContext) -> bool:
        return ctx in self._captcha_queue

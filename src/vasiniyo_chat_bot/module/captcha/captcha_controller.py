from dataclasses import dataclass
from dataclasses import replace

from vasiniyo_chat_bot.event_queue import EVENTS
from vasiniyo_chat_bot.event_queue import add_task
from vasiniyo_chat_bot.event_queue import cancel_task
from vasiniyo_chat_bot.event_queue import logger
from vasiniyo_chat_bot.module.captcha.captcha_payload_factory import CaptchaPayload
from vasiniyo_chat_bot.module.captcha.captcha_response_factory import (
    CaptchaResponseFactory,
)
from vasiniyo_chat_bot.module.captcha.captcha_service import CaptchaService
from vasiniyo_chat_bot.module.dto import CallbackContext
from vasiniyo_chat_bot.module.dto import MessageContext
from vasiniyo_chat_bot.module.dto import UserContext
from vasiniyo_chat_bot.module.renderer import Renderer
from vasiniyo_chat_bot.module.user_service import UserService


@dataclass(frozen=True)
class _CaptchaSession:
    task_id: str
    message_id: int


@dataclass(frozen=True)
class CaptchaCallbackContext(CallbackContext):
    payload: CaptchaPayload


class CaptchaController:
    _captcha_queue: dict[tuple[int, int], _CaptchaSession] = {}

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

    def handle_new_user(self, ctx: UserContext):
        user = self._captcha_service.generate_captcha(ctx.chat_id, ctx.user_id)
        freq = self._captcha_service.captcha_properties().validate.update_freq
        timestamps = list(range(freq, user.time_left + 1, freq))
        logger.info(
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
        response = self._response_factory.captcha(user)
        captcha_message_id = self._renderer.send(response, ctx)
        session = _CaptchaSession(task_id, captcha_message_id)
        self._captcha_queue[ctx.chat_id, ctx.user_id] = session

    def handle_verify_captcha(self, ctx: MessageContext):
        self._renderer.delete(ctx)
        if self._captcha_service.validate_captcha(ctx.chat_id, ctx.user_id, ctx.text):
            self.handle_captcha_success(ctx)
            return
        user = self._captcha_service.increase_failed_attempts(ctx.chat_id, ctx.user_id)
        if self._captcha_service.attempts_remained(user):
            self.update_captcha_message(ctx)
        else:
            self.handle_captcha_failure(ctx, "Max attempts used")

    def handle_captcha_button_press(self, ctx: CaptchaCallbackContext):
        payload = ctx.payload
        if ctx.user_id != payload.user_id:
            response = self._response_factory.no_access()
            self._renderer.alert(response, ctx)
            return
        user = self._captcha_service.regenerate_captcha(ctx.chat_id, ctx.user_id)
        session = self._captcha_queue.get((ctx.chat_id, ctx.user_id))
        if session:
            response = self._response_factory.captcha(user)
            self._renderer.edit(response, replace(ctx, message_id=session.message_id))

    def handle_captcha_success(self, ctx: UserContext):
        session = self._captcha_queue.pop((ctx.chat_id, ctx.user_id), None)
        if session:
            cancel_task(session.task_id, silently=True)
            response = self._response_factory.passed_captcha()
            self._captcha_service.remove_user(ctx.chat_id, ctx.user_id)
            self._renderer.delete(
                UserContext(ctx.user_id, ctx.chat_id, session.message_id, None)
            )
            self._renderer.send(response, replace(ctx, message_id=session.message_id))

    def handle_captcha_failure(self, ctx: UserContext, reason: str):
        session = self._captcha_queue.get((ctx.chat_id, ctx.user_id))
        if session:
            self._captcha_queue.pop((ctx.chat_id, ctx.user_id), None)
            self._captcha_service.remove_user(ctx.chat_id, ctx.user_id)
            response = self._response_factory.failed_captcha(reason)
            self._renderer.edit_caption(
                response, replace(ctx, message_id=session.message_id)
            )
        self._user_service.ban(ctx)

    def update_captcha_message(self, ctx: UserContext):
        timer = self._captcha_service.captcha_properties().validate.timer
        session = self._captcha_queue.get((ctx.chat_id, ctx.user_id))
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
        return (ctx.chat_id, ctx.user_id) in self._captcha_queue

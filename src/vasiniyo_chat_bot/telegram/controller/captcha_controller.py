from dataclasses import dataclass

from telebot.types import CallbackQuery, Message

from vasiniyo_chat_bot.event_queue import EVENTS, add_task, cancel_task, logger
from vasiniyo_chat_bot.module.captcha.captcha_service import CaptchaService
from vasiniyo_chat_bot.safely_bot_utils import extract_field, parse_json
from vasiniyo_chat_bot.telegram.bot_service import BotService
from vasiniyo_chat_bot.telegram.dto import Action, Field
from vasiniyo_chat_bot.telegram.renderer.captcha_renderer import CaptchaRenderer


@dataclass(frozen=True)
class CaptchaSession:
    task_id: str
    message_id: int


class CaptchaController:
    captcha_queue: dict[tuple[int, int], CaptchaSession] = {}

    def __init__(
        self,
        captcha_service: CaptchaService,
        bot_service: BotService,
        captcha_renderer: CaptchaRenderer,
    ) -> None:
        self.captcha_service = captcha_service
        self.bot_service = bot_service
        self.captcha_renderer = captcha_renderer

    def are_captcha_user(self, message: Message) -> bool:
        return (message.chat.id, message.from_user.id) in self.captcha_queue

    def handle_new_user(self, message: Message):
        chat_id = message.chat.id
        for member in message.new_chat_members:
            user_id = member.id
            if member.is_bot:
                logger.info(
                    "captcha_new_user",
                    extra={"user_id": user_id, "details": "user is bot, skipping"},
                )
                continue
            captcha_user = self.captcha_service.generate_captcha(chat_id, user_id)
            message_id = self.captcha_renderer.send_captcha(captcha_user, message)
            freq = self.captcha_service.captcha_properties.validate.update_freq
            timestamps = list(range(freq, captcha_user.time_left + 1, freq))
            logger.info(
                "captcha_new_user",
                extra={
                    "chat_id": captcha_user.chat_id,
                    "user_id": captcha_user.user_id,
                    "attempts": captcha_user.failed_attempts,
                    "time_seconds": captcha_user.time_left,
                    "answer": captcha_user.answer,
                },
            )
            task_id = add_task(
                timestamps=timestamps,
                default=lambda: self.update_captcha_message(chat_id, user_id),
                conditional_funcs={
                    "on_success": lambda: self.handle_captcha_failure(
                        user_id, "Время вышло", chat_id
                    ),
                    "on_cancel": lambda: self.handle_captcha_failure(
                        user_id, "Капча отменена", chat_id
                    ),
                },
            )
            self.captcha_queue[chat_id, user_id] = CaptchaSession(task_id, message_id)

    def handle_verify_captcha(self, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        self.bot_service.delete_message(chat_id, message.id)
        if self.captcha_service.validate_captcha(chat_id, user_id, message.text):
            self.handle_captcha_success(chat_id, user_id)
            return
        captcha_user = self.captcha_service.increase_failed_attempts(chat_id, user_id)
        if self.captcha_service.attempts_remained(captcha_user):
            self.update_captcha_message(chat_id, user_id)
        else:
            self.handle_captcha_failure(user_id, "Max attempts used", chat_id)

    def handle_captcha_button_press(self, call: CallbackQuery):
        message = call.message
        user_id = call.from_user.id
        chat_id = message.chat.id
        payload_user_id = extract_field(parse_json(call.data), Field.USER_ID)
        if call.from_user.id != payload_user_id:
            self.bot_service.answer_callback_query(
                "Эти кнопки были не для тебя!", call.id
            )
            return
        captcha_user = self.captcha_service.regenerate_captcha(chat_id, user_id)
        session = self.captcha_queue.get((chat_id, user_id))
        if session:
            self.captcha_renderer.regenerate_captcha(
                captcha_user, chat_id, session.message_id
            )

    def handle_captcha_success(self, chat_id: int, user_id: int):
        session = self.captcha_queue.pop((chat_id, user_id), None)
        if session:
            cancel_task(session.task_id, silently=True)
            self.captcha_service.remove_user(chat_id, user_id)
            self.captcha_renderer.passed_captcha(chat_id, session.message_id)

    def handle_captcha_failure(self, user_id: int, reason: str, chat_id: int):
        timer = self.captcha_service.captcha_properties.validate.timer
        session = self.captcha_queue.get((chat_id, user_id))
        if session:
            event = EVENTS.get(session.task_id, {})
            event_offset = event.get("offset", timer)
            event_time_left = timer - event_offset
            captcha_user = self.captcha_service.update_captcha_time_left(
                chat_id, user_id, event_time_left
            )
            self.captcha_queue.pop((chat_id, user_id), None)
            self.captcha_service.remove_user(chat_id, user_id)
            self.captcha_renderer.failed_captcha(
                captcha_user, chat_id, session.message_id, reason
            )
        self.bot_service.ban_chat_member(chat_id, user_id)

    def update_captcha_message(self, chat_id: int, user_id: int):
        timer = self.captcha_service.captcha_properties.validate.timer
        session = self.captcha_queue.get((chat_id, user_id))
        if session:
            event = EVENTS.get(session.task_id, {})
            event_offset = event.get("offset", timer)
            event_time_left = timer - event_offset
            captcha_user = self.captcha_service.update_captcha_time_left(
                chat_id, user_id, event_time_left
            )
            self.captcha_renderer.next_captcha_state(
                user_id, captcha_user, chat_id, session.message_id
            )

    def is_captcha_user(self, message: Message) -> bool:
        return (message.chat.id, message.from_user.id) in self.captcha_queue

    @staticmethod
    def has_captcha_payload(call: CallbackQuery) -> bool:
        payload = parse_json(call.data)
        return payload.get(Field.ACTION_TYPE.value) == Action.CAPTCHA_UPDATE.value

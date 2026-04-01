from dataclasses import replace
import logging
import random
import string

from vasiniyo_chat_bot.module.captcha.captcha_repository import CaptchaRepository
from vasiniyo_chat_bot.module.captcha.dto import Captcha, CaptchaUser

logger = logging.getLogger(__name__)


class CaptchaService:
    def __init__(
        self, captcha_properties: Captcha, captcha_repository: CaptchaRepository
    ):
        self.captcha_properties = captcha_properties
        self.captcha_repository = captcha_repository
        self._raw_banned = captcha_properties.gen.banned_symbols
        banned = {c.lower() for c in self._raw_banned} | {
            c.upper() for c in self._raw_banned
        }
        self._allowed_symbols = [
            c for c in (string.ascii_letters + string.digits) if c not in banned
        ]

    def attempts_remained(self, user: CaptchaUser):
        return user.failed_attempts < self.captcha_properties.validate.attempts

    def remove_user(self, chat_id: int, user_id: int):
        return self.captcha_repository.remove(chat_id, user_id)

    def generate_captcha(self, chat_id: int, user_id: int) -> CaptchaUser:
        time_left = self.captcha_properties.validate.timer
        failed_attempts = 0
        text = self._generate_captcha_text()
        user = CaptchaUser(
            chat_id=chat_id,
            user_id=user_id,
            failed_attempts=failed_attempts,
            time_left=time_left,
            answer=text,
        )
        return self.captcha_repository.save(chat_id, user_id, user)

    def regenerate_captcha(self, chat_id: int, user_id: int):
        user = self.captcha_repository.find(chat_id, user_id)
        if not user:
            return None
        upd_user = replace(user, answer=self._generate_captcha_text())
        return self.captcha_repository.save(chat_id, user_id, upd_user)

    def increase_failed_attempts(
        self, chat_id: int, user_id: int
    ) -> CaptchaUser | None:
        user = self.captcha_repository.find(chat_id, user_id)
        if not user:
            return None
        upd_user = replace(user, failed_attempts=user.failed_attempts + 1)
        return self.captcha_repository.save(chat_id, user_id, upd_user)

    def validate_captcha(self, chat_id: int, user_id: int, user_input: str | None):
        user = self.captcha_repository.find(chat_id, user_id)
        if not user:
            return None
        return user_input and user_input.strip().lower() == user.answer.lower()

    def update_captcha_time_left(
        self, chat_id: int, user_id: int, event_time_left: int
    ):
        user = self.captcha_repository.find(chat_id, user_id)
        if not user:
            return None
        upd_user = replace(user, time_left=max(0, event_time_left))
        return self.captcha_repository.save(chat_id, user_id, upd_user)

    def _generate_captcha_text(self):
        length = self.captcha_properties.gen.length
        return "".join(random.choices(self._allowed_symbols, k=length))

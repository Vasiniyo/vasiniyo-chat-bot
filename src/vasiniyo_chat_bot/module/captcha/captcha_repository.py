from vasiniyo_chat_bot.module.captcha.dto import CaptchaUser


class CaptchaRepository:
    _captcha_users: dict[tuple[int, int], CaptchaUser] = {}

    def save(self, chat_id: int, user_id: int, user: CaptchaUser) -> CaptchaUser:
        self._captcha_users[chat_id, user_id] = user
        return user

    def find(self, chat_id: int, user_id: int) -> CaptchaUser | None:
        return self._captcha_users.get((chat_id, user_id))

    def remove(self, chat_id: int, user_id: int) -> CaptchaUser | None:
        return self._captcha_users.pop((chat_id, user_id), None)

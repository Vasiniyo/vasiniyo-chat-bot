from vasiniyo_chat_bot.module.captcha.dto import CaptchaUser


class CaptchaRepository:
    CAPTCHA_USERS: dict[tuple[int, int], CaptchaUser] = {}

    def save(self, chat_id: int, user_id: int, user: CaptchaUser) -> CaptchaUser:
        self.CAPTCHA_USERS[chat_id, user_id] = user
        return user

    def find(self, chat_id: int, user_id: int) -> CaptchaUser | None:
        return self.CAPTCHA_USERS.get((chat_id, user_id))

    def remove(self, chat_id: int, user_id: int) -> CaptchaUser | None:
        return self.CAPTCHA_USERS.pop((chat_id, user_id), None)

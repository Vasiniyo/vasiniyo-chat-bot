from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from vasiniyo_chat_bot.telegram.payload.captcha_payload_factory import (
    CaptchaPayloadFactory,
)


class CaptchaKeyboardFactory:
    def __init__(self, payload_factory: CaptchaPayloadFactory):
        self._payload_factory = payload_factory

    def update_button(self, user_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Обновить капчу",
                        callback_data=self._payload_factory.update_captcha(user_id),
                    )
                ]
            ]
        )

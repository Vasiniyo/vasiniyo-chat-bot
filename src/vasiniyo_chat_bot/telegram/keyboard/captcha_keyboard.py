from telebot.types import InlineKeyboardButton
from telebot.types import InlineKeyboardMarkup

from vasiniyo_chat_bot.module.dto import Action
from vasiniyo_chat_bot.module.payload_factory import PayloadFactory


class CaptchaKeyboardFactory:
    @staticmethod
    def captcha_menu(user_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            keyboard=[[CaptchaKeyboardFactory._update_button(user_id)]]
        )

    @staticmethod
    def _update_button(user_id: int):
        return InlineKeyboardButton(
            text="🔄 Обновить капчу",
            callback_data=PayloadFactory.dump(Action.CAPTCHA_UPDATE, user_id),
        )

from io import BytesIO
import json
import logging

from PIL import Image, ImageOps
from captcha.image import ImageCaptcha
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from vasiniyo_chat_bot.module.captcha.dto import Captcha, CaptchaUser
from vasiniyo_chat_bot.telegram.bot_service import BotService
from vasiniyo_chat_bot.telegram.dto import Action, Field

logger = logging.getLogger(__name__)


class CaptchaRenderer:

    @staticmethod
    def _create_update_captcha_payload(user_id: int):
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.CAPTCHA_UPDATE.value,
                Field.USER_ID.value: user_id,
            }
        )

    def _create_update_captcha_markup(self, user_id: int):
        return InlineKeyboardMarkup(
            keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Обновить капчу",
                        callback_data=self._create_update_captcha_payload(user_id),
                    )
                ]
            ]
        )

    def __init__(self, bot_service: BotService, captcha_properties: Captcha):
        self.bot_service = bot_service
        self.captcha_properties = captcha_properties

    def send_captcha(self, captcha_user: CaptchaUser, message: Message) -> int:
        chat_id = message.chat.id
        image = self._generate_captcha_image(captcha_user.answer)
        caption = self._build_caption(
            captcha_user.time_left, captcha_user.failed_attempts
        )
        message = self.bot_service.send_photo(
            image,
            chat_id,
            caption=caption,
            reply_markup=self._create_update_captcha_markup(captcha_user.user_id),
        )
        return message.id

    def next_captcha_state(
        self, user_id: int, captcha_user: CaptchaUser, chat_id: int, message_id: int
    ):
        new_caption = self._build_caption(
            captcha_user.time_left, captcha_user.failed_attempts
        )
        try:
            self.bot_service.edit_message_caption(
                chat_id,
                message_id,
                new_caption,
                reply_markup=self._create_update_captcha_markup(captcha_user.user_id),
            )
        except Exception as e:
            logger.error(e)
            logger.debug("Skipping update caption for user", {"user_id": user_id})

    def regenerate_captcha(
        self, captcha_user: CaptchaUser, chat_id: int, message_id: int
    ):
        image = self._generate_captcha_image(captcha_user.answer)
        caption = self._build_caption(
            captcha_user.time_left, captcha_user.failed_attempts
        )
        self.bot_service.edit_message_media(
            image,
            chat_id,
            message_id,
            caption,
            reply_markup=self._create_update_captcha_markup(captcha_user.user_id),
        )

    def failed_captcha(
        self, captcha_user: CaptchaUser, chat_id: int, message_id: int, reason: str
    ):
        caption = self._build_caption(
            captcha_user.time_left, captcha_user.failed_attempts, reason
        )
        self.bot_service.edit_message_caption(chat_id, message_id, caption)

    def passed_captcha(self, chat_id: int, message_id: int):
        self.bot_service.delete_message(chat_id, message_id)
        self.bot_service.send_message(
            self.captcha_properties.greeting_message, chat_id, is_disabled_preview=False
        )

    def _build_caption(
        self, time_left, failed_attempts, failed_reason: str | None = None
    ):
        validate = self.captcha_properties.validate
        attempts_left = max(0, validate.attempts - failed_attempts)
        pct = ((validate.timer - time_left) * 100 // validate.timer) // 5 * 5
        filled = min(validate.bar_length, pct * validate.bar_length // 100)
        bar = f"[{'=' * filled}>{' ' * (validate.bar_length - filled - 1)}]"
        return (
            f"🧩 CAPTCHA Verification\n"
            f"{bar}\n"
            f"Осталось времени: {time_left // 5 * 5}с\n"
            f"Осталось попыток: {attempts_left}"
            + (f"\n❌ {failed_reason}" if failed_reason else "")
        )

    def _generate_captcha_image(self, text):
        image = ImageCaptcha(fonts=[self.captcha_properties.gen.font_path])
        image.character_rotate = (
            -self.captcha_properties.gen.max_rotation,
            self.captcha_properties.gen.max_rotation,
        )
        image = Image.open(image.generate(text))
        padded = ImageOps.expand(
            image,
            border=(
                0,
                self.captcha_properties.gen.margins_width,
                0,
                self.captcha_properties.gen.margins_width,
            ),
            fill=self.captcha_properties.gen.margins_color,
        )
        buf = BytesIO()
        padded.save(buf, format="PNG")
        buf.seek(0)
        return buf

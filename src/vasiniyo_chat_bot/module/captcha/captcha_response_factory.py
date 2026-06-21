from dataclasses import replace
from io import BytesIO
import logging

from PIL import Image
from PIL import ImageOps
from captcha.image import ImageCaptcha

from vasiniyo_chat_bot.module.captcha.dto import Captcha
from vasiniyo_chat_bot.module.captcha.dto import CaptchaUser
from vasiniyo_chat_bot.module.dto import Response
from vasiniyo_chat_bot.module.titles.dto import CaptchaMenu

logger = logging.getLogger(__name__)


class CaptchaResponseFactory:
    def __init__(self, captcha_properties: Captcha):
        self._captcha_properties = captcha_properties

    def captcha(self, user: CaptchaUser) -> Response:
        image = self._generate_captcha_image(user.answer)
        return replace(self.description(user), picture=image)

    def description(self, user: CaptchaUser):
        text = self._build_caption(user.time_left, user.failed_attempts)
        return Response(text_units=text, menu=CaptchaMenu())

    def passed_captcha(self):
        text = self._captcha_properties.greeting_message
        return Response(text_units=text)

    @staticmethod
    def failed_captcha(reason: str):
        text = f"\n❌ {reason}"
        return Response(text_units=text)

    @staticmethod
    def no_access():
        return Response(text_units="Эти кнопки были не для тебя!")

    def _build_caption(self, time_left, failed_attempts):
        validate = self._captcha_properties.validate
        attempts_left = max(0, validate.attempts - failed_attempts)
        pct = ((validate.timer - time_left) * 100 // validate.timer) // 5 * 5
        filled = min(validate.bar_length, pct * validate.bar_length // 100)
        bar = f"[{'=' * filled}>{' ' * (validate.bar_length - filled - 1)}]"
        return (
            f"🧩 CAPTCHA Verification\n"
            f"{bar}\n"
            f"Осталось времени: {time_left // 5 * 5}с\n"
            f"Осталось попыток: {attempts_left}"
        )

    def _generate_captcha_image(self, text):
        image = ImageCaptcha(fonts=[self._captcha_properties.gen.font_path])
        image.character_rotate = (
            -self._captcha_properties.gen.max_rotation,
            self._captcha_properties.gen.max_rotation,
        )
        image = Image.open(image.generate(text))
        padded = ImageOps.expand(
            image,
            border=(
                0,
                self._captcha_properties.gen.margins_width,
                0,
                self._captcha_properties.gen.margins_width,
            ),
            fill=self._captcha_properties.gen.margins_color,
        )
        buf = BytesIO()
        padded.save(buf, format="PNG")
        buf.seek(0)
        return buf

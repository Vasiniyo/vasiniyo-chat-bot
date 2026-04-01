from vasiniyo_chat_bot import assets
from vasiniyo_chat_bot.module.captcha.dto import Captcha, Gen, Validate


class CaptchaReader:
    def __init__(self, section: dict[str, any]) -> None:
        self._section = section

    def load(self) -> Captcha:
        captcha_properties = self._section.get("captcha_properties", {})
        gen = captcha_properties.get("gen", {})
        validate = captcha_properties.get("validate", {})
        return Captcha(
            gen=Gen(
                length=gen.get("length", 5),
                banned_symbols=gen.get("banned_symbols", "104aqiol"),
                max_rotation=gen.get("max_rotation", 45),
                margins_width=gen.get("margins_width", 12),
                margins_color=gen.get("margins_color", "#0e1621"),
                font_path=gen.get(
                    assets.font("font_path"),
                    assets.font("GoMonoNerdFontMono-Regular.ttf"),
                ),
            ),
            validate=Validate(
                timer=validate.get("timer", 90),
                update_freq=validate.get("update_freq", 10),
                attempts=validate.get("attempts", 5),
                bar_length=validate.get("bar_length", 20),
            ),
            content_types=captcha_properties.get("content_types", ["text"]),
            greeting_message=(
                self._section.get(
                    "welcome_message_for_new_members", "Добро пожаловать в чат!"
                )
            ),
        )

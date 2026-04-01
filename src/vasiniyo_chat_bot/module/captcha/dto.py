from dataclasses import dataclass


@dataclass
class Gen:
    length: int
    banned_symbols: str
    max_rotation: int
    margins_width: int
    margins_color: str
    font_path: str


@dataclass
class Validate:
    timer: int
    update_freq: int
    attempts: int
    bar_length: int


@dataclass
class Captcha:
    gen: Gen
    validate: Validate
    content_types: list[str]
    greeting_message: str


@dataclass(frozen=True)
class CaptchaUser:
    chat_id: int
    user_id: int
    failed_attempts: int
    time_left: int
    answer: str

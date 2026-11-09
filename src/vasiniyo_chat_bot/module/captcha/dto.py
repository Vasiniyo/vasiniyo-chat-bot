from __future__ import annotations

from dataclasses import dataclass

from injector import inject

from vasiniyo_chat_bot.module.dto import Menu


@dataclass(frozen=True)
class Gen:
    length: int
    banned_symbols: str
    max_rotation: int
    margins_width: int
    margins_color: str
    font_path: str


@dataclass(frozen=True)
class Validate:
    timer: int
    update_freq: int
    attempts: int
    bar_length: int


@inject
@dataclass(frozen=True)
class Captcha:
    gen: Gen
    validate: Validate
    greeting_message: str


@dataclass(frozen=True)
class CaptchaUser:
    chat_id: int
    user_id: int
    failed_attempts: int
    time_left: int
    answer: str


@dataclass(frozen=True)
class CaptchaMenu(Menu): ...

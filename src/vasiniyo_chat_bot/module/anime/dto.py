from __future__ import annotations

from dataclasses import dataclass

from vasiniyo_chat_bot.module.dto import Menu


@dataclass(frozen=True)
class Anime:
    link: str | None


@dataclass(frozen=True)
class AnimeGenreMenu(Menu): ...

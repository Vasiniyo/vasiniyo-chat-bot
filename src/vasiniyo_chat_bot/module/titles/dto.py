from __future__ import annotations

from dataclasses import dataclass

from vasiniyo_chat_bot.module.dto import CallbackContext
from vasiniyo_chat_bot.module.dto import Menu
from vasiniyo_chat_bot.module.dto import Pageable
from vasiniyo_chat_bot.module.titles.titles_payload_factory import TitlesPayload


@dataclass(frozen=True)
class AdjectiveGroup:
    base: list[str]
    male_ending: str
    female_ending: str
    neuter_ending: str
    plural_ending: str


@dataclass(frozen=True)
class NounGroup:
    base: list[str]
    singular_ending: str
    plural_ending: str


@dataclass(frozen=True)
class Nouns:
    male: list[NounGroup]
    female: list[NounGroup]
    neuter: list[NounGroup]


@dataclass(frozen=True)
class CustomTitles:
    adjectives: list[AdjectiveGroup]
    nouns: Nouns


@dataclass(frozen=True)
class AnimeGenreMenu(Menu): ...


@dataclass(frozen=True)
class CaptchaMenu(Menu): ...


@dataclass(frozen=True)
class RenameMenu(Menu):
    title: str | None
    d6: bool
    random_d6: bool
    steal_menu: bool
    exchange_menu: bool
    titles_bag: bool


@dataclass(frozen=True)
class TitleInfo:
    id: int
    user_id: int
    title: str
    is_inventory: bool
    username: str | None = None


@dataclass(frozen=True)
class StealMenu(Menu):
    chat_id: int
    titles: list[TitleInfo]
    page: int
    has_prev_pages: bool
    has_more_pages: bool


@dataclass(frozen=True)
class StealResult:
    actor_id: int
    target_id: int
    target_title: str
    actor_title: str
    changed: bool


@dataclass(frozen=True)
class TitleChanged:
    title: str
    changed: bool


@dataclass(frozen=True)
class TitleExchanged:
    title: str | None
    extra_rolls: int
    changed: bool


@dataclass(frozen=True)
class GiftRecipientInfo:
    user_id: int
    username: str | None = None


@dataclass(frozen=True)
class GiftRecipientsMenu(Menu):
    chat_id: int
    recipients: list[GiftRecipientInfo]
    page: int
    has_prev_pages: bool
    has_more_pages: bool


@dataclass(frozen=True)
class GiftTitlesMenu(Menu):
    chat_id: int
    target_user_id: int
    titles: list[TitleInfo]
    page: int
    has_prev_pages: bool
    has_more_pages: bool


@dataclass(frozen=True)
class TitlesBagItemView:
    user_id: int
    titles_bag_id: int
    title: str


@dataclass(frozen=True)
class TitlesBagMenu(Pageable, Menu):
    items: list[TitlesBagItemView]


@dataclass(frozen=True)
class ExchangeTitleMenu(Pageable, Menu):
    items: list[TitlesBagItemView]


@dataclass(frozen=True)
class TitlesCallbackContext(CallbackContext):
    payload: TitlesPayload

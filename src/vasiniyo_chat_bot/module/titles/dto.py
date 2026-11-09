from __future__ import annotations

from dataclasses import dataclass

from injector import inject

from vasiniyo_chat_bot.module.dto import Menu
from vasiniyo_chat_bot.module.dto import Pageable


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


@inject
@dataclass(frozen=True)
class CustomTitles:
    adjectives: list[AdjectiveGroup]
    nouns: Nouns


@dataclass(frozen=True)
class RenameMenu(Menu):
    rolling_title: str | None
    has_d6_menu: bool
    has_random_d6_menu: bool
    has_steal_menu: bool
    has_exchange_menu: bool
    has_titles_bag_menu: bool


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
    has_return_button: bool = True


@dataclass(frozen=True)
class FailedStealMenu(Menu):
    chat_id: int
    user_id: int
    extra_attempts: int
    target_title: TitleInfo
    has_exchange_menu: bool


@dataclass(frozen=True)
class FailedRollMenu(Menu):
    title: str
    extra_attempts: int
    has_exchange_menu: bool


@dataclass(frozen=True)
class Title:
    user_id: int | None
    value: str | None


@dataclass(frozen=True)
class SuccessSteal:
    actor_title: Title
    target_title: Title


@dataclass(frozen=True)
class TitleExchanged:
    titles: list[str]
    extra_rolls: int


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
    has_return_button: bool = True


@dataclass(frozen=True)
class GiftTitlesMenu(Menu):
    chat_id: int
    target_user_id: int
    titles: list[TitleInfo]
    page: int
    has_prev_pages: bool
    has_more_pages: bool
    has_return_button: bool = True


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

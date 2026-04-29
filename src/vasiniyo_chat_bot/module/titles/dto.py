from dataclasses import dataclass


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
class RenameMenu:
    title: str | None
    d6: bool
    random_d6: bool
    steal_menu: bool
    titles_bag: bool


@dataclass(frozen=True)
class TitleInfo:
    id: int
    user_id: int
    title: str
    is_inventory: bool
    username: str | None = None


@dataclass(frozen=True)
class StealMenu:
    chat_id: int
    titles: list[TitleInfo]
    page: int
    has_prev_pages: bool
    has_more_pages: bool


@dataclass(frozen=True)
class TitlesBagMenu:
    titles: list[tuple[int, int, str]]
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
class GiftRecipientInfo:
    user_id: int
    username: str | None = None


@dataclass(frozen=True)
class GiftRecipientsMenu:
    chat_id: int
    recipients: list[GiftRecipientInfo]
    page: int
    has_prev_pages: bool
    has_more_pages: bool


@dataclass(frozen=True)
class GiftTitlesMenu:
    chat_id: int
    target_user_id: int
    titles: list[TitleInfo]
    page: int
    has_prev_pages: bool
    has_more_pages: bool

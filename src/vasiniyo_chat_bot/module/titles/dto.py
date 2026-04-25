from dataclasses import dataclass


@dataclass
class CustomTitles:
    adjectives: list[str]
    nouns: list[str]
    weights: list[int]


@dataclass(frozen=True)
class RenameMenu:
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

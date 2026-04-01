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
class StealMenu:
    titles: list[tuple[int, str]]
    page: int
    has_prev_pages: bool
    has_more_pages: bool


@dataclass(frozen=True)
class TitlesBagMenu:
    titles: list[tuple[int, str]]
    page: int
    has_prev_pages: bool
    has_more_pages: bool


@dataclass(frozen=True)
class StealSuccessResult:
    actor_id: int
    target_id: int
    target_title: str
    actor_title: str


@dataclass(frozen=True)
class StealFailureResult:
    pass


@dataclass(frozen=True)
class TitleChanged:
    title: str
    changed: bool

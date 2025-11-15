from dataclasses import dataclass
import logging
from typing import (
    Callable,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

from config import lang

logger = logging.getLogger(__name__)

T = TypeVar("T")
U = TypeVar("U")


@dataclass
class Pair(Generic[T, U]):

    x: T
    y: U

    def __iter__(self):
        yield self.x
        yield self.y

    def __getitem__(self, index):
        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        else:
            raise IndexError("Pair index out of range (0-1)")

    def __len__(self):
        return 2


@dataclass
class Tier:
    @dataclass
    class Locale:

        phrases: Dict[str, List[str]]  # {lang: [phrases]}

    value_range: Pair[int, int]
    locale: Locale


# =============================================================================
# WinValue
# =============================================================================


class WinValue:
    @dataclass
    class Locale:
        goal_templates: Dict[str, str]  # {lang: "processed goal text"}

    def __init__(
        self,
        type: Literal["max", "min", "exact"],
        value: Callable[[], int],
        locale: Locale,
    ):
        self.type = type
        self._value_callable = value
        self._cached_value: Optional[int] = None
        self.locale = locale

    @property
    def value(self) -> int:
        if self._cached_value is None:
            self._cached_value = self._value_callable()
        return self._cached_value

    def __repr__(self):
        return f"WinValue(type={self.type!r}, value={self.value})"

    def get_goal_text(self, language: str) -> str:
        return self.locale.goal_templates.get(language, "")

    @staticmethod
    def create_exact(exact_value: int, locale: "WinValue.Locale") -> "WinValue":
        return WinValue(type="exact", value=lambda: exact_value, locale=locale)

    @staticmethod
    def create_from_schema(
        win_value_spec: Union[str, Tuple[str, int]],
        min_range: int,
        max_range: int,
        locale: "WinValue.Locale",
    ) -> "WinValue":
        if isinstance(win_value_spec, str):
            if win_value_spec == "min":
                return WinValue("min", lambda: min_range, locale)
            elif win_value_spec == "max":
                return WinValue("max", lambda: max_range, locale)
            else:
                raise ValueError(
                    f"Invalid win_value string: '{win_value_spec}'. "
                    f"Expected 'min' or 'max'"
                )
        elif isinstance(win_value_spec, tuple):
            if len(win_value_spec) != 2:
                raise ValueError(
                    f"Tuple win_value must have 2 elements, got {len(win_value_spec)}"
                )
            if win_value_spec[0] != "exact":
                raise ValueError(
                    f"Tuple win_value must be ('exact', value), "
                    f"got ('{win_value_spec[0]}', ...)"
                )
            return WinValue.create_exact(win_value_spec[1], locale)
        else:
            raise ValueError(
                f"win_value must be str or tuple, got {type(win_value_spec).__name__}"
            )


class PlayableCategory:

    @dataclass
    class Locale:
        name: Dict[str, str]  # {lang: "category name"}
        units: Dict[str, str]  # {lang: "unit name"}

    def __init__(
        self,
        name: str,
        tiers: Tuple[Tier, ...],
        win_value: WinValue,
        locale: Locale,
        continuous: bool = True,
    ):
        self.name = name
        self.tiers = tiers
        self.win_value = win_value
        self.locale = locale
        self.continuous = continuous
        self._min_range: int
        self._max_range: int
        self._all_values: List[int] = []

        self.__post_init__()

    def __post_init__(self):
        if not self.tiers:
            raise ValueError("Category must have at least one tier")

        for idx, tier in enumerate(self.tiers):
            if tier.value_range.x > tier.value_range.y:
                raise ValueError(
                    f"Invalid range in tier {idx}: "
                    f"{tier.value_range.x} > {tier.value_range.y}"
                )

        self.tiers = tuple(sorted(self.tiers, key=lambda tier: tier.value_range.x))
        self._min_range = min(tier.value_range.x for tier in self.tiers)
        self._max_range = max(tier.value_range.y for tier in self.tiers)

        self._build_all_values_view()

        validation_errors = []
        validation_errors.extend(self._validate_all_ranges())
        validation_errors.extend(self._validate_locales())
        validation_errors.extend(self._validate_win_value())

        if validation_errors:
            error_message = "Validation failed:\n" + "\n".join(
                f"- {error}" for error in validation_errors
            )
            raise ValueError(error_message)

    def _build_all_values_view(self):

        def values_generator():
            for tier in self.tiers:
                for value in range(tier.value_range.x, tier.value_range.y + 1):
                    yield value

        self._values_generator = values_generator
        self._total_values_count = sum(
            tier.value_range.y - tier.value_range.x + 1 for tier in self.tiers
        )

    def _validate_all_ranges(self) -> List[str]:
        errors = []

        for i in range(len(self.tiers) - 1):
            current = self.tiers[i]
            next_tier = self.tiers[i + 1]

            current_end = current.value_range.y
            next_start = next_tier.value_range.x

            if current_end >= next_start:
                errors.append(
                    f"Ranges overlap: Tier {i} ({current.value_range.x}, {current_end}) "
                    f"and Tier {i + 1} ({next_start}, {next_tier.value_range.y})"
                )
            elif self.continuous and current_end + 1 != next_start:
                errors.append(
                    f"Gap between ranges: Tier {i} ({current.value_range.x}, {current_end}) "
                    f"and Tier {i + 1} ({next_start}, {next_tier.value_range.y}). "
                    f"Use continuous=False to allow gaps."
                )

        return errors

    def _validate_locales(self) -> List[str]:
        errors = []

        global lang
        required_language = lang

        if required_language not in self.locale.name:
            errors.append(
                f"Category locale 'name' missing required language '{required_language}'"
            )

        if required_language not in self.locale.units:
            errors.append(
                f"Category locale 'units' missing required language '{required_language}'"
            )

        for idx, tier in enumerate(self.tiers):
            if required_language not in tier.locale.phrases:
                errors.append(
                    f"Tier {idx + 1} locale missing required language '{required_language}'"
                )
            else:
                phrases = tier.locale.phrases.get(required_language, [])
                if not phrases or len(phrases) == 0:
                    errors.append(
                        f"Tier {idx + 1} has no phrases for language '{required_language}'"
                    )

        if required_language not in self.win_value.locale.goal_templates:
            errors.append(
                f"WinValue locale missing required language '{required_language}'"
            )
        else:
            goal_text = self.win_value.locale.goal_templates.get(required_language, "")
            if not goal_text:
                errors.append(
                    f"WinValue has empty goal template for language '{required_language}'"
                )

        return errors

    def _validate_win_value(self) -> List[str]:
        errors = []

        try:
            actual_value = self.win_value.value
        except Exception as e:
            errors.append(f"Failed to compute win_value: {e}")
            return errors

        if self.win_value.type == "exact":
            if not any(
                tier.value_range.x <= actual_value <= tier.value_range.y
                for tier in self.tiers
            ):
                range_str = self._format_ranges()
                errors.append(
                    f"win_value {actual_value} is not within any tier's range. "
                    f"Valid ranges: {range_str}"
                )

        return errors

    def _format_ranges(self) -> str:
        if not self.tiers:
            return "[]"

        if self.continuous:
            return f"[{self._min_range}..{self._max_range}]"
        else:
            ranges = [
                f"[{tier.value_range.x}..{tier.value_range.y}]" for tier in self.tiers
            ]
            return " ".join(ranges)

    def __repr__(self):
        tier_lines = []
        for tier in self.tiers:
            min_val, max_val = tier.value_range
            tier_lines.append(
                f"Range {min_val}-{max_val}, Phrases: {tier.locale.phrases}"
            )

        tiers_str = "\n".join(tier_lines)
        return (
            f"Category: {self.name}\n"
            f"{tiers_str}\n"
            f"continuous: {self.continuous}\n"
            f"win_value: {self.win_value}"
        )

    @classmethod
    def create(
        cls,
        name: str,
        tiers_num: int,
        ranges: Union[Callable[[int], Tuple[int, int]], Dict[int, Tuple[int, int]]],
        phrases: Dict[str, Dict[int, List[str]]],
        win_value: Union[str, Tuple[str, int]],
        locale: Dict[str, Dict[str, str]],
        win_locale: Optional[Dict[str, List[str]]] = None,
        continuous: bool = True,
    ) -> Optional["PlayableCategory"]:

        from commands.play.category_builder import create_category

        return create_category(
            name=name,
            tiers_num=tiers_num,
            ranges=ranges,
            phrases=phrases,
            win_value=win_value,
            locale=locale,
            win_locale=win_locale,
            continuous=continuous,
        )

    def get_tier_for_value(self, value: int) -> Optional[Tier]:
        if not self.tiers:
            return None

        if value < self._min_range or value > self._max_range:
            return None

        left, right = 0, len(self.tiers) - 1

        while left <= right:
            mid = (left + right) // 2
            tier = self.tiers[mid]

            if tier.value_range.x <= value <= tier.value_range.y:
                return tier
            elif value < tier.value_range.x:
                right = mid - 1
            else:
                left = mid + 1

        return None

    def get_win_goal_text(self, language: str = lang) -> str:
        return self.win_value.get_goal_text(language)

    def get_random_value(self, seed: int) -> int:
        import random

        rng = random.Random(seed)
        random_index = rng.randint(0, self._total_values_count - 1)

        current_index = 0
        for tier in self.tiers:
            tier_size = tier.value_range.y - tier.value_range.x + 1
            if current_index + tier_size > random_index:
                value_offset = random_index - current_index
                return tier.value_range.x + value_offset
            current_index += tier_size

        return self._min_range

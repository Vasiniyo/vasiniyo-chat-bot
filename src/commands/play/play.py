from dataclasses import dataclass, fields
from functools import cached_property
import logging
from typing import (
    Any, Callable, Dict, Generic, List, Literal, Optional, Tuple, TypeVar, Union,
)

from config import lang
from logger import logger

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
        phrases: Dict[str, List[str]]

    value_range: Pair[int, int]
    locale: Locale


class WinValue:
    """Represents the winning condition for a category."""

    def __init__(self, type: Literal["max", "min", "exact"], value: Callable[[], int]):
        """
        Args:
            type: The type of winning condition
            value: A callable that returns the winning value (will be cached)
        """
        self.type = type
        self._value_callable = value
        self._cached_value: Optional[int] = None

    @property
    def value(self) -> int:
        """Get the winning value (cached after first access)."""
        if self._cached_value is None:
            self._cached_value = self._value_callable()
        return self._cached_value

    def __repr__(self):
        return f"WinValue(type={self.type!r}, value={self.value})"

    @staticmethod
    def create_min(category: "PlayableCategory") -> "WinValue":
        """Factory method for min win value."""
        return WinValue(type="min", value=lambda: category._min_range)

    @staticmethod
    def create_max(category: "PlayableCategory") -> "WinValue":
        """Factory method for max win value."""
        return WinValue(type="max", value=lambda: category._max_range)

    @staticmethod
    def create_exact(exact_value: int) -> "WinValue":
        """Factory method for exact win value."""
        return WinValue(type="exact", value=lambda: exact_value)


class PlayableCategory:
    @dataclass
    class Locale:
        name: Dict[str, str]
        units: Dict[str, str]
        win_goal: Dict[str, str]

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

    def _build_all_values_view(self):
        def values_generator():
            for tier in self.tiers:
                for value in range(tier.value_range.x, tier.value_range.y + 1):
                    yield value

        self._values_generator = values_generator

        self._total_values_count = sum(
            tier.value_range.y - tier.value_range.x + 1 for tier in self.tiers
        )

    def __post_init__(self):
        """Validate the category after creation."""
        if not self.tiers:
            return

        for idx, tier in enumerate(self.tiers):
            if tier.value_range.x > tier.value_range.y:
                raise ValueError(
                    f"Invalid range in tier {idx}: {tier.value_range.x} > {tier.value_range.y}"
                )

        self.tiers = tuple(sorted(self.tiers, key=lambda tier: tier.value_range.x))

        self._min_range = min(tier.value_range.x for tier in self.tiers)
        self._max_range = max(tier.value_range.y for tier in self.tiers)

        self._build_all_values_view()

        validation_errors = self._validate_all_ranges()
        locale_errors = self._validate_locales()
        win_value_errors = self._validate_win_value()

        validation_errors.extend(locale_errors)
        validation_errors.extend(win_value_errors)

        if validation_errors:
            error_message = "Validation failed:\n" + "\n".join(
                f"- {error}" for error in validation_errors
            )
            raise ValueError(error_message)

    def __repr__(self):
        tier_lines = []
        for tier in self.tiers:
            min_val, max_val = tier.value_range
            tier_lines.append(
                f"Range {min_val}-{max_val}, Phrases: {tier.locale.phrases}"
            )

        tiers_str = "\n".join(tier_lines)
        return (
            f"{tiers_str}\ncontinuous: {self.continuous}\nwin_value: {self.win_value}"
        )

    def _validate_win_value(self) -> List[str]:
        """Validate that the win_value is valid for this category's ranges."""
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

    def _validate_all_ranges(self) -> List[str]:
        """Perform all range validations and return list of error messages."""
        errors = []

        for i in range(len(self.tiers) - 1):
            current = self.tiers[i]
            next_tier = self.tiers[i + 1]

            current_end = current.value_range.y
            next_start = next_tier.value_range.x

            # Check for overlap
            if current_end >= next_start:
                errors.append(
                    f"Ranges overlap: Tier {i} ({current.value_range.x}, {current_end}) "
                    f"and Tier {i + 1} ({next_start}, {next_tier.value_range.y})"
                )
            # Check for gap
            elif self.continuous and current_end + 1 != next_start:
                errors.append(
                    f"Gap between ranges: Tier {i} ({current.value_range.x}, {current_end}) "
                    f"and Tier {i + 1} ({next_start}, {next_tier.value_range.y}). "
                    f"Use continuous=False to allow gaps."
                )

        return errors

    def _validate_locales(self) -> List[str]:
        """Validate that all tiers have phrases for all languages and locale consistency."""
        errors = []

        if not self.tiers:
            errors.append("no tiers to validate against")
            return errors

        global lang
        required_language = lang

        # Check each field in PlayableCategory.Locale has the required language
        locale_fields = fields(PlayableCategory.Locale)
        for field in locale_fields:
            field_value = getattr(self.locale, field.name)
            if required_language not in field_value:
                errors.append(
                    f"'{field.name}' is missing required language '{required_language}'"
                )

        # Check each tier has phrases for the required language
        for idx, tier in enumerate(self.tiers):
            if required_language not in tier.locale.phrases:
                errors.append(
                    f"Tier {idx + 1} is missing required language '{required_language}'"
                )
            else:
                phrases = tier.locale.phrases.get(required_language, [])
                if not phrases or len(phrases) == 0:
                    errors.append(
                        f"Tier {idx + 1} has no phrases for language '{required_language}'"
                    )

        return errors

    def _format_ranges(self) -> str:
        """Format ranges for display"""
        if not self.tiers:
            return "[]"

        if self.continuous:
            return f"[{self._min_range}..{self._max_range}]"
        else:
            # Non-continuous: show each tier's range
            # TODO contact connecting ones
            ranges = [
                f"[{tier.value_range.x}..{tier.value_range.y}]" for tier in self.tiers
            ]
            return " ".join(ranges)

    def get_formatted_win_goal(self, language: str = lang) -> str:
        """
        Get the formatted win goal message for the given language.
        Handles place holders:
            - @range: formats available range for category.
            - @value: gets the value for the win.
        """
        if language not in self.locale.win_goal:
            return ""

        template = self.locale.win_goal[language]

        template = template.replace("@range", self._format_ranges())
        template = template.replace("@value", str(self.win_value.value))

        return template

    @staticmethod
    def _validate_locale_schema(
        locale: Dict[str, Dict[str, str]], name: str, win_type: str
    ) -> List[str]:
        """Validate locale dictionary schema. Uses defaults for win_goal if not present"""
        from commands.play.play_config import win_goal_locale

        errors = []
        locale_fields = {field.name for field in fields(PlayableCategory.Locale)}

        if not locale:
            errors.append("locale is empty")
            return errors

        for lang_code, data in locale.items():
            if not isinstance(data, dict):
                errors.append(
                    f"locale['{lang_code}'] must be a dictionary, got {type(data).__name__}"
                )
                continue

            for field_name in locale_fields:
                if field_name not in data:
                    if field_name == "win_goal":
                        if (
                            lang_code in win_goal_locale
                            and win_type in win_goal_locale[lang_code]
                        ):
                            default_goal = "".join(win_goal_locale[lang_code][win_type])
                            data["win_goal"] = default_goal
                            logger.info(
                                f"Using default '{win_type}' winner message"
                                f"for category '{name}' in language '{lang_code}'"
                            )
                        else:
                            errors.append(
                                f"locale['{lang_code}'] is missing 'win_goal'"
                                f"and no default available for win_type '{win_type}'"
                            )
                    else:
                        errors.append(
                            f"locale['{lang_code}'] is missing '{field_name}' key"
                        )
                elif not isinstance(data[field_name], str):
                    errors.append(
                        f"locale['{lang_code}']['{field_name}'] must be a string, "
                        f"got {type(data[field_name]).__name__}"
                    )

        return errors

    @staticmethod
    def _validate_phrases_schema(
        phrases: Dict[str, Dict[int, List[str]]], tiers_num: int
    ) -> List[str]:
        """Validate phrases dictionary schema."""
        errors = []

        if not phrases:
            errors.append("phrases is empty")
            return errors

        for lang, tier_data in phrases.items():
            if not isinstance(tier_data, dict):
                errors.append(
                    f"phrases['{lang}'] must be a dictionary, got {type(tier_data).__name__}"
                )
                continue

            # Check that all tiers from 1 to tiers_num exist
            for tier_num in range(1, tiers_num + 1):
                if tier_num not in tier_data:
                    errors.append(f"phrases['{lang}'] is missing tier {tier_num}")
                    continue

                tier_phrases = tier_data[tier_num]
                if not isinstance(tier_phrases, list):
                    errors.append(
                        f"phrases['{lang}'][{tier_num}] must be a list, got {type(tier_phrases).__name__}"
                    )
                    continue

                if len(tier_phrases) == 0:
                    errors.append(
                        f"phrases['{lang}'][{tier_num}] must have at least one phrase"
                    )

        return errors

    @classmethod
    def create(
        cls,
        name: str,
        tiers_num: int,
        ranges: Union[Callable[[int], Tuple[int, int]], Dict[int, Tuple[int, int]]],
        phrases: Dict[str, Dict[int, List[str]]],
        win_value: Union[str, Tuple[str, int]],
        locale: Dict[str, Dict[str, str]],
        continuous: bool = True,
    ) -> Optional["PlayableCategory"]:
        """
        Factory method to create PlayableCategory with validation.
        Returns None if validation fails (logs error with highest priority).

        Args:
            name: Category name
            tiers_num: Number of tiers
            ranges: Either a function (tier_num -> (min, max)) or dict {tier_num: (min, max)}
            phrases: {"lang": {tier_num: [phrases]}}
            win_value: Either "min", "max", or ("exact", value)
            locale: {"lang": {"name": "...", "units": "...",
                              "win_goal": "min" | "max"| ["exact", value:int]}}
            continuous: If True, ranges must be continuous (no gaps). If False, gaps are allowed.
        """
        if isinstance(win_value, str):
            win_type = win_value
        elif isinstance(win_value, tuple):
            win_type = win_value[0]
        else:
            win_type = "unknown"  # should never hit it

        # Validate locale schema
        # NOTE: uses defaults for win_goal
        locale_errors = cls._validate_locale_schema(locale, name, win_type)
        if locale_errors:
            logger.critical(
                f"CRITICAL: Category '{name}' has invalid locale configuration!\n"
                f"{'=' * 80}\n"
                f"Errors:\n" + "\n".join(f"  • {err}" for err in locale_errors) + "\n"
                f"Received locale: {locale}\n"
                f"Expected schema: {{'<lang>': {{'name': '<string>', 'units': '<string>', 'win_goal': '<string>' (optional)}}}}\n"
                f"{'=' * 80}\n"
                f"SKIPPING CATEGORY '{name}'"
            )
            return None

        # Validate phrases schema
        phrases_errors = cls._validate_phrases_schema(phrases, tiers_num)
        if phrases_errors:
            logger.critical(
                f"CRITICAL: Category '{name}' has invalid phrases configuration!\n"
                f"{'=' * 80}\n"
                f"Errors:\n" + "\n".join(f"  • {err}" for err in phrases_errors) + "\n"
                f"Received phrases structure: {{{', '.join(phrases.keys())}: {{<tier_num>: [phrases]}}}}\n"
                f"Expected: Each language must have phrases for tiers 1-{tiers_num}\n"
                f"{'=' * 80}\n"
                f"SKIPPING CATEGORY '{name}'"
            )
            return None

        if callable(ranges):
            range_dict = {i + 1: ranges(i + 1) for i in range(tiers_num)}
        else:
            range_dict = ranges.copy()

        tier_objects = []
        for tier_num in range(1, tiers_num + 1):
            tier_range = range_dict.get(tier_num, (0, 0))

            tier_phrases_by_lang = {}
            for lang, tier_data in phrases.items():
                tier_phrases_by_lang[lang] = tier_data.get(tier_num, [])

            tier_objects.append(
                Tier(
                    value_range=Pair(tier_range[0], tier_range[1]),
                    locale=Tier.Locale(phrases=tier_phrases_by_lang),
                )
            )

        locale_names = {lang: data["name"] for lang, data in locale.items()}
        locale_units = {lang: data["units"] for lang, data in locale.items()}
        locale_win_goal = {lang: data["win_goal"] for lang, data in locale.items()}

        locale_obj = cls.Locale(
            name=locale_names, units=locale_units, win_goal=locale_win_goal
        )

        # Create a temporary category to pass to WinValue factory methods
        # We'll set win_value to None initially, then update it
        temp_category = cls.__new__(cls)
        temp_category.name = name
        temp_category.tiers = tuple(tier_objects)
        temp_category.locale = locale_obj
        temp_category.continuous = continuous
        temp_category._all_values = []

        # Calculate ranges before creating WinValue
        if temp_category.tiers:
            temp_category.tiers = tuple(
                sorted(temp_category.tiers, key=lambda tier: tier.value_range.x)
            )
            temp_category._min_range = min(
                tier.value_range.x for tier in temp_category.tiers
            )
            temp_category._max_range = max(
                tier.value_range.y for tier in temp_category.tiers
            )

        # Parse win_value and create WinValue object
        try:
            if isinstance(win_value, str):
                if win_value == "min":
                    win_value_obj = WinValue.create_min(temp_category)
                elif win_value == "max":
                    win_value_obj = WinValue.create_max(temp_category)
                else:
                    logger.critical(
                        f"CRITICAL: Category '{name}' has invalid win_value '{win_value}'!\n"
                        f"Expected 'min', 'max', or ('exact', value)\n"
                        f"SKIPPING CATEGORY '{name}'"
                    )
                    return None
            elif isinstance(win_value, tuple) and len(win_value) == 2:
                win_type_str, exact_value = win_value
                if win_type_str != "exact":
                    logger.critical(
                        f"CRITICAL: Category '{name}' has invalid tuple win_value!\n"
                        f"Expected ('exact', value), got ('{win_type_str}', {exact_value})\n"
                        f"SKIPPING CATEGORY '{name}'"
                    )
                    return None
                win_value_obj = WinValue.create_exact(exact_value)
            else:
                logger.critical(
                    f"CRITICAL: Category '{name}' has invalid win_value type!\n"
                    f"Expected str or tuple, got {type(win_value).__name__}\n"
                    f"SKIPPING CATEGORY '{name}'"
                )
                return None
        except Exception as e:
            logger.critical(
                f"CRITICAL: Category '{name}' has invalid win_value configuration!\n"
                f"Error: {e}\n"
                f"SKIPPING CATEGORY '{name}'"
            )
            return None

        try:
            return cls(
                name=name,
                tiers=tuple(tier_objects),
                win_value=win_value_obj,
                locale=locale_obj,
                continuous=continuous,
            )
        except ValueError as e:
            logger.critical(
                f"CRITICAL: Category '{name}' failed validation during initialization!\n"
                f"Error: {e}\n"
                f"SKIPPING CATEGORY '{name}'"
            )
            return None

    def get_tier_for_value(self, value: int) -> Tier | None:
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
            else:  # value > tier.value_range.y
                left = mid + 1

        return None

    def get_win_value(self) -> int:
        """Get the winning value for this category."""
        return self.win_value.value

    def get_random_value(self, seed: int) -> int:
        """Get a random value for a user based on their seed."""
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

        # Should never hit here
        return self._min_range

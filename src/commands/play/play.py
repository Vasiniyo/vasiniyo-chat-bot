from dataclasses import dataclass, fields
import logging
from typing import Any, Callable, Dict, Generic, List, Optional, Tuple, TypeVar, Union

from config import lang
from src.commands.play.play_config import win_goal_locale
from src.logger import logger

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
        win_value: Union[str, int],
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

    # TODO validate that locale have all values for each language
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
        validation_errors.extend(locale_errors)

        if validation_errors:
            error_message = "Validation failed:\n" + "\n".join(
                f"- {error}" for error in validation_errors
            )
            raise ValueError(error_message)

        if isinstance(self.win_value, str):
            if self.win_value not in ["min", "max"]:
                raise ValueError(f"winner_value must be 'min', 'max', or an integer")
        elif isinstance(self.win_value, int):
            if self.win_value < self._min_range or self.win_value > self._max_range:
                raise ValueError(
                    f"winner_value {self.win_value} is outside range [{self._min_range}, {self._max_range}]"
                )
            if not any(
                tier.value_range.x <= self.win_value <= tier.value_range.y
                for tier in self.tiers
            ):
                raise ValueError(
                    f"winner_value {self.win_value} is not within any tier's range"
                )

    # TODO add locale to repr
    def __repr__(self):
        tier_lines = []
        for tier in self.tiers:
            min_val, max_val = tier.value_range
            tier_lines.append(
                f"Range {min_val}-{max_val}, Phrases: {tier.locale.phrases}"
            )

        tiers_str = "\n".join(tier_lines)
        return f"{tiers_str}\ncontinuous: {self.continuous}"

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

    @staticmethod
    def _validate_locale_schema(locale: Dict[str, Dict[str, str]], name) -> List[str]:
        """Validate locale dictionary schema."""
        errors = []
        locale_fields = {field.name for field in fields(PlayableCategory.Locale)}

        if not locale:
            errors.append("locale is empty")
            return errors

        for lang, data in locale.items():
            if not isinstance(data, dict):
                errors.append(
                    f"locale['{lang}'] must be a dictionary, got {type(data).__name__}"
                )
                continue

            for field_name in locale_fields:
                if field_name not in data:
                    if field_name != "win_goal":
                        errors.append(f"locale['{lang}'] is missing '{field_name}' key")
                    else:
                        logger.info(
                            "Using default winner message for the category %s", name
                        )
                        locale[field_name] = {lang: win_goal_locale[lang]}
                elif not isinstance(data[field_name], str):
                    errors.append(
                        f"locale['{lang}']['{field_name}'] must be a string, "
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
        win_value: Union[str, int],
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
            locale: {"lang": {"name": "...", "units": "...", "win_goal" = ".." | default}}
            continuous: If True, ranges must be continuous (no gaps). If False, gaps are allowed.
        """
        # Validate locale schema
        locale_errors = cls._validate_locale_schema(locale, name)
        if locale_errors:
            logger.critical(
                f"CRITICAL: Category '{name}' has invalid locale configuration!\n"
                f"{'=' * 80}\n"
                f"Errors:\n" + "\n".join(f"  • {err}" for err in locale_errors) + "\n"
                f"Received locale: {locale}\n"
                f"Expected schema: {{'<lang>': {{'name': '<string>', 'units': '<string>'}}}}\n"
                f"{'=' * 80}\n"
                f"SKIPPING CATEGORY '{name}'"
            )

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
        locale_obj = cls.Locale(name=locale_names, units=locale_units)

        return cls(
            name=name,
            tiers=tuple(tier_objects),
            winner_value=win_value,
            locale=locale_obj,
            continuous=continuous,
        )

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

    def get_winner_value(self) -> int:
        """Get the winning value for this category."""
        if isinstance(self.win_value, int):
            return self.win_value
        elif self.win_value == "min":
            return self._min_range
        elif self.win_value == "max":
            return self._max_range

        raise ValueError(f"Invalid winner_value: {self.win_value}")

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

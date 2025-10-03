from dataclasses import dataclass
import logging
from typing import Any, Callable, Dict, Generic, List, Optional, Tuple, TypeVar, Union

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
    value_range: Pair[int, int]
    phrases: Tuple[str, ...]


class PlayableCategory:
    def __init__(
        self,
        name: str,
        tiers: Tuple[Tier, ...],
        winner_value: Union[str, int] = "max",
        continuous: bool = True,
    ):
        self.name = name
        self.tiers = tiers
        self.winner_value = winner_value
        self.continuous = continuous
        self._min_range: int
        self._max_range: int
        self._all_values: List[int] = []

        self.__post_init__()

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
        if validation_errors:
            error_message = "Validation failed:\n" + "\n".join(
                f"- {error}" for error in validation_errors
            )
            raise ValueError(error_message)

        if isinstance(self.winner_value, str):
            if self.winner_value not in ["min", "max"]:
                raise ValueError(f"winner_value must be 'min', 'max', or an integer")
        elif isinstance(self.winner_value, int):
            if (
                self.winner_value < self._min_range
                or self.winner_value > self._max_range
            ):
                raise ValueError(
                    f"winner_value {self.winner_value} is outside range [{self._min_range}, {self._max_range}]"
                )
            if not any(
                tier.value_range.x <= self.winner_value <= tier.value_range.y
                for tier in self.tiers
            ):
                raise ValueError(
                    f"winner_value {self.winner_value} is not within any tier's range"
                )

    def __repr__(self):
        tier_lines = []
        for tier in self.tiers:
            min_val, max_val = tier.value_range
            tier_lines.append(f"Range {min_val}-{max_val}, Phrases: {tier.phrases}")

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

    def _build_all_values_view(self):
        def values_generator():
            for tier in self.tiers:
                for value in range(tier.value_range.x, tier.value_range.y + 1):
                    yield value

        self._values_generator = values_generator

        self._total_values_count = sum(
            tier.value_range.y - tier.value_range.x + 1 for tier in self.tiers
        )

    @classmethod
    def create(
        cls,
        name: str,
        tiers_num: int,
        ranges: Union[Callable[[int], Tuple[int, int]], Dict[int, Tuple[int, int]]],
        phrases: Dict[int, List[str]],
        winner_value: Union[str, int] = "max",
        continuous: bool = True,
    ) -> "PlayableCategory":
        """
        Factory method to create PlayableCategory.
        Validation happens in __post_init__.

        Args:
            name: Category name
            tiers_num: Number of tiers
            ranges: Either a function (tier_num -> (min, max)) or dict {tier_num: (min, max)}
            phrases: Dict {tier_num: [phrase1, phrase2, ...]}
            continuous: If True, ranges must be continuous (no gaps). If False, gaps are allowed.
        """

        if callable(ranges):
            range_dict = {i + 1: ranges(i + 1) for i in range(tiers_num)}
        else:
            range_dict = ranges.copy()

        tier_objects = []
        for tier_num in range(1, tiers_num + 1):
            tier_range = range_dict.get(tier_num, (0, 0))
            tier_phrases = phrases.get(tier_num, [""])

            tier_objects.append(
                Tier(
                    value_range=Pair(tier_range[0], tier_range[1]),
                    phrases=tuple(tier_phrases),
                )
            )

        return cls(
            name=name,
            tiers=tuple(tier_objects),
            winner_value=winner_value,
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
        if isinstance(self.winner_value, int):
            return self.winner_value
        elif self.winner_value == "min":
            return self._min_range
        elif self.winner_value == "max":
            return self._max_range

        raise ValueError(f"Invalid winner_value: {self.winner_value}")

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

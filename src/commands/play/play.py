from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, List, Tuple, TypeVar, Union

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
    i: int
    value_range: Pair[int, int]
    phrases: Tuple[str, ...]


class PlayableCategory:
    def __init__(self, name: str, tiers: Tuple[Tier, ...], continuous: bool = True):
        self.name = name
        self.tiers = tiers
        self.continuous = continuous
        self._min_range = None
        self._max_range = None

        self.__post_init__()

    def __post_init__(self):
        """Validate the category after creation."""
        if not self.tiers:
            return

        for tier in self.tiers:
            if tier.value_range.x > tier.value_range.y:
                raise ValueError(
                    f"Invalid range in tier {tier.i}: {tier.value_range.x} > {tier.value_range.y}"
                )

        sorted_tiers = sorted(self.tiers, key=lambda tier: tier.value_range.x)
        self.tiers = tuple(
            Tier(i=idx, value_range=tier.value_range, phrases=tier.phrases)
            for idx, tier in enumerate(sorted_tiers)
        )

        self._min_range = min(tier.value_range.x for tier in self.tiers)
        self._max_range = max(tier.value_range.y for tier in self.tiers)

        validation_errors = self._validate_all_ranges()
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
                f"Tier {tier.i}: Range {min_val}-{max_val}, Phrases: {tier.phrases}"
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

    @classmethod
    def create(
        cls,
        name: str,
        tiers_num: int,
        ranges: Union[Callable[[int], Tuple[int, int]], Dict[int, Tuple[int, int]]],
        phrases: Dict[int, List[str]],
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
                    i=tier_num,
                    value_range=Pair(tier_range[0], tier_range[1]),
                    phrases=tuple(tier_phrases),
                )
            )

        return cls(name=name, tiers=tuple(tier_objects), continuous=continuous)

    def get_tier_for_value(self, value: int) -> Tier | None:
        """Get the tier that contains the given value using binary search."""
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

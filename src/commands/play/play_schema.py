from dataclasses import dataclass
import logging
from typing import Any, Callable, Dict, List, Tuple, Union

logger = logging.getLogger(__name__)


@dataclass
class SchemaValidationResult:

    locale_errors: List[str]
    phrases_errors: List[str]
    win_value_errors: List[str]
    ranges_errors: List[str]
    win_locale_errors: List[str]

    @property
    def has_errors(self) -> bool:
        return bool(
            self.locale_errors
            or self.phrases_errors
            or self.win_value_errors
            or self.ranges_errors
            or self.win_locale_errors
        )

    @property
    def all_errors(self) -> List[str]:
        """Flat list of all errors."""
        return (
            self.locale_errors
            + self.phrases_errors
            + self.win_value_errors
            + self.ranges_errors
            + self.win_locale_errors
        )


def extract_win_type(win_value: Union[str, Tuple[str, int]]) -> str:
    if isinstance(win_value, str):
        return win_value
    elif isinstance(win_value, tuple) and len(win_value) >= 1:
        return win_value[0]
    return "unknown"


def validate_win_value_schema(win_value: Union[str, Tuple[str, int]]) -> List[str]:
    errors = []

    if isinstance(win_value, str):
        if win_value not in ("min", "max"):
            errors.append(
                f"Invalid string win_value: '{win_value}'. Expected 'min' or 'max'"
            )
    elif isinstance(win_value, tuple):
        if len(win_value) != 2:
            errors.append(f"Tuple win_value must have 2 elements, got {len(win_value)}")
        elif win_value[0] != "exact":
            errors.append(
                f"Tuple win_value must be ('exact', value), got ('{win_value[0]}', ...)"
            )
        elif not isinstance(win_value[1], int):
            errors.append(
                f"Exact win_value must be int, got {type(win_value[1]).__name__}"
            )
    else:
        errors.append(f"win_value must be str or tuple, got {type(win_value).__name__}")

    return errors


def validate_ranges_schema(
    ranges: Union[Callable[[int], Tuple[int, int]], Dict[int, Tuple[int, int]]],
    tiers_num: int,
) -> List[str]:
    errors = []

    if callable(ranges):
        return []

    if not isinstance(ranges, dict):
        errors.append(f"ranges must be dict or callable, got {type(ranges).__name__}")
        return errors

    for tier_num in range(1, tiers_num + 1):
        if tier_num not in ranges:
            errors.append(f"ranges missing tier {tier_num}")
            continue

        tier_range = ranges[tier_num]
        if not isinstance(tier_range, tuple) or len(tier_range) != 2:
            errors.append(f"ranges[{tier_num}] must be a 2-tuple, got {tier_range}")
            continue

        min_val, max_val = tier_range
        if not isinstance(min_val, int) or not isinstance(max_val, int):
            errors.append(f"ranges[{tier_num}] must contain ints")

    return errors


def validate_phrases_schema(
    phrases: Dict[str, Dict[int, List[str]]], tiers_num: int
) -> List[str]:
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

        for tier_num in range(1, tiers_num + 1):
            if tier_num not in tier_data:
                errors.append(f"phrases['{lang}'] is missing tier {tier_num}")
                continue

            tier_phrases = tier_data[tier_num]
            if not isinstance(tier_phrases, list):
                errors.append(
                    f"phrases['{lang}'][{tier_num}] must be a list, "
                    f"got {type(tier_phrases).__name__}"
                )
                continue

            if len(tier_phrases) == 0:
                errors.append(
                    f"phrases['{lang}'][{tier_num}] must have at least one phrase"
                )

    return errors


def validate_category_locale_schema(locale: Dict[str, Dict[str, str]]) -> List[str]:
    errors = []

    if not isinstance(locale, dict):
        errors.append(f"locale must be a dictionary, got {type(locale).__name__}")
        return errors

    if not locale:
        # Empty locale is allowed at schema level, will be caught in post-init
        return errors

    required_fields = {"name", "units"}

    for lang_code, data in locale.items():
        if not isinstance(data, dict):
            errors.append(
                f"locale['{lang_code}'] must be a dictionary, got {type(data).__name__}"
            )
            continue

        for field_name in required_fields:
            if field_name not in data:
                errors.append(
                    f"locale['{lang_code}'] is missing required field '{field_name}'"
                )
            elif not isinstance(data[field_name], str):
                errors.append(
                    f"locale['{lang_code}']['{field_name}'] must be a string, "
                    f"got {type(data[field_name]).__name__}"
                )

    return errors


def validate_win_locale_schema(win_locale: Dict[str, List[str]]) -> List[str]:
    errors = []

    if win_locale is None:
        return errors  # NOTE: Optional field - defaults will be applied

    if not isinstance(win_locale, dict):
        errors.append(
            f"win_locale must be a dictionary, got {type(win_locale).__name__}"
        )
        return errors

    for lang_code, template_parts in win_locale.items():
        if not isinstance(template_parts, list):
            errors.append(
                f"win_locale['{lang_code}'] must be a list, "
                f"got {type(template_parts).__name__}"
            )
            continue

        if len(template_parts) == 0:
            errors.append(
                f"win_locale['{lang_code}'] must have at least one template part"
            )
            continue

        for idx, part in enumerate(template_parts):
            if not isinstance(part, str):
                errors.append(
                    f"win_locale['{lang_code}'][{idx}] must be a string, "
                    f"got {type(part).__name__}"
                )

    return errors


def validate_full_schema(
    name: str,
    tiers_num: int,
    ranges: Union[Callable[[int], Tuple[int, int]], Dict[int, Tuple[int, int]]],
    phrases: Dict[str, Dict[int, List[str]]],
    win_value: Union[str, Tuple[str, int]],
    locale: Dict[str, Dict[str, str]],
    win_locale: Dict[str, List[str]] = None,
) -> SchemaValidationResult:
    result = SchemaValidationResult(
        locale_errors=[],
        phrases_errors=[],
        win_value_errors=[],
        ranges_errors=[],
        win_locale_errors=[],
    )

    result.win_value_errors = validate_win_value_schema(win_value)
    result.ranges_errors = validate_ranges_schema(ranges, tiers_num)
    result.phrases_errors = validate_phrases_schema(phrases, tiers_num)
    result.locale_errors = validate_category_locale_schema(locale)
    result.win_locale_errors = validate_win_locale_schema(win_locale)

    return result


def log_schema_errors(name: str, validation: SchemaValidationResult):
    error_sections = []

    if validation.locale_errors:
        error_sections.append(
            "Category Locale errors:\n"
            + "\n".join(f"  • {err}" for err in validation.locale_errors)
        )

    if validation.phrases_errors:
        error_sections.append(
            "Phrases errors:\n"
            + "\n".join(f"  • {err}" for err in validation.phrases_errors)
        )

    if validation.win_value_errors:
        error_sections.append(
            "Win value errors:\n"
            + "\n".join(f"  • {err}" for err in validation.win_value_errors)
        )

    if validation.ranges_errors:
        error_sections.append(
            "Ranges errors:\n"
            + "\n".join(f"  • {err}" for err in validation.ranges_errors)
        )

    if validation.win_locale_errors:
        error_sections.append(
            "Win locale errors:\n"
            + "\n".join(f"  • {err}" for err in validation.win_locale_errors)
        )

    logger.critical(
        f"CRITICAL: Category '{name}' has invalid schema!\n"
        f"{'=' * 80}\n" + "\n\n".join(error_sections) + f"\n{'=' * 80}\n"
        f"SKIPPING CATEGORY '{name}'"
    )

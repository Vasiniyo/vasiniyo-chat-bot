from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING, Callable, Dict, List, Literal, Optional, Tuple, Union

if TYPE_CHECKING:
    from commands.play.play import PlayableCategory, Tier, WinValue

logger = logging.getLogger(__name__)


@dataclass
class CategoryBuildResult:
    name: str
    category: Optional[PlayableCategory]
    phase_failed: Optional[Literal["schema", "build", "post_init"]]
    errors: List[str]

    @property
    def success(self) -> bool:
        return self.category is not None


class PlayableCategoryBuilder:
    def __init__(self, name: str):
        self.name = name

        # Configuration state (validated schema data)
        self._tiers_num: Optional[int] = None
        self._ranges: Optional[Union[Callable, Dict]] = None
        self._phrases: Optional[Dict[str, Dict[int, List[str]]]] = None
        self._win_value_spec: Optional[Union[str, Tuple[str, int]]] = None
        self._locale_spec: Optional[Dict[str, Dict[str, str]]] = None
        self._win_locale_spec: Optional[Dict[str, List[str]]] = None
        self._continuous: bool = True

        # Derived state (computed during build)
        self.d_computed_ranges: Dict[int, Tuple[int, int]] = {}
        self.d_min_range: int = 0
        self.d_max_range: int = 0

    def with_tiers(
        self,
        tiers_num: int,
        ranges: Union[Callable[[int], Tuple[int, int]], Dict[int, Tuple[int, int]]],
    ) -> PlayableCategoryBuilder:
        self._tiers_num = tiers_num
        self._ranges = ranges
        return self

    def with_phrases(
        self, phrases: Dict[str, Dict[int, List[str]]]
    ) -> PlayableCategoryBuilder:
        self._phrases = phrases
        return self

    def with_win_value(
        self, win_value: Union[str, Tuple[str, int]]
    ) -> PlayableCategoryBuilder:
        self._win_value_spec = win_value
        return self

    def with_locale(self, locale: Dict[str, Dict[str, str]]) -> PlayableCategoryBuilder:
        self._locale_spec = locale
        return self

    def with_win_locale(
        self, win_locale: Optional[Dict[str, List[str]]]
    ) -> PlayableCategoryBuilder:
        self._win_locale_spec = win_locale
        return self

    def is_continuous(self, value: bool = True) -> PlayableCategoryBuilder:
        self._continuous = value
        return self

    def build(self) -> PlayableCategory:
        from commands.play.play import PlayableCategory

        self._validate_builder_state()
        self._compute_ranges()

        win_value_obj = self._build_win_value()
        tier_objects = self._build_tiers()
        locale_obj = self._build_category_locale()

        return PlayableCategory(
            name=self.name,
            tiers=tuple(tier_objects),
            win_value=win_value_obj,
            locale=locale_obj,
            continuous=self._continuous,
        )

    def _validate_builder_state(self):
        missing = []
        if self._tiers_num is None:
            missing.append("tiers_num")
        if self._ranges is None:
            missing.append("ranges")
        if self._phrases is None:
            missing.append("phrases")
        if self._win_value_spec is None:
            missing.append("win_value")
        if self._locale_spec is None:
            missing.append("locale")

        if missing:
            raise RuntimeError(
                f"Builder incomplete: missing {', '.join(missing)}. "
                f"Did you forget to call with_* methods?"
            )

    def _compute_ranges(self):
        assert self._tiers_num is not None
        assert self._ranges is not None

        if callable(self._ranges):
            self.d_computed_ranges = {
                i: self._ranges(i) for i in range(1, self._tiers_num + 1)
            }
        else:
            self.d_computed_ranges = self._ranges.copy()

        sorted_ranges = sorted(self.d_computed_ranges.values(), key=lambda r: r[0])
        self.d_min_range = sorted_ranges[0][0]
        self.d_max_range = sorted_ranges[-1][1]

    def _build_win_value(self) -> WinValue:
        from commands.play.play import WinValue

        assert self._win_value_spec is not None

        win_type = self._extract_win_type()
        win_locale_obj = self._build_win_locale(win_type)

        return WinValue.create_from_schema(
            win_value_spec=self._win_value_spec,
            min_range=self.d_min_range,
            max_range=self.d_max_range,
            locale=win_locale_obj,
        )

    def _build_win_locale(self, win_type: str) -> WinValue.Locale:
        from commands.play.play import WinValue
        from commands.play.play_config import win_goal_locale

        goal_templates = {}

        if self._win_locale_spec:
            languages_to_process = set(self._win_locale_spec.keys())
        else:
            languages_to_process = set(win_goal_locale.keys())

        for lang_code in languages_to_process:
            if self._win_locale_spec and lang_code in self._win_locale_spec:
                template_parts = self._win_locale_spec[lang_code]
                logger.debug(
                    f"Using CUSTOM win_locale for category '{self.name}' "
                    f"in language '{lang_code}'"
                )
            elif (
                lang_code in win_goal_locale and win_type in win_goal_locale[lang_code]
            ):
                template_parts = win_goal_locale[lang_code][win_type]
                logger.debug(
                    f"Using DEFAULT '{win_type}' goal template "
                    f"for category '{self.name}' in language '{lang_code}'"
                )
            else:
                logger.info(
                    f"No win_locale found for category '{self.name}' "
                    f"in language '{lang_code}' with win_type '{win_type}'. "
                    f"Using empty template."
                )
                template_parts = []

            processed = self._process_locale_tokens(template_parts, win_type)
            goal_templates[lang_code] = processed

        return WinValue.Locale(goal_templates=goal_templates)

    def _process_locale_tokens(self, template_parts: List[str], win_type: str) -> str:
        result = ""

        for part in template_parts:
            # TODO: if non-continuous needs better range creation
            if part == "@range":
                if self.d_min_range == self.d_max_range:
                    result += str(self.d_min_range)
                else:
                    result += f"{self.d_min_range}-{self.d_max_range}"
            elif part == "@value":
                if win_type == "exact" and isinstance(self._win_value_spec, tuple):
                    result += str(self._win_value_spec[1])
                elif win_type == "max":
                    result += str(self.d_max_range)
                elif win_type == "min":
                    result += str(self.d_min_range)
                else:
                    result += "@value"
            else:
                result += part

        return result

    def _build_tiers(self) -> List[Tier]:
        from commands.play.play import Pair, Tier

        assert self._tiers_num is not None
        assert self._phrases is not None

        tier_objects = []

        for tier_num in range(1, self._tiers_num + 1):
            tier_range = self.d_computed_ranges[tier_num]

            tier_phrases_by_lang = {}
            for lang_code, tier_data in self._phrases.items():
                tier_phrases_by_lang[lang_code] = tier_data.get(tier_num, [])

            tier_objects.append(
                Tier(
                    value_range=Pair(tier_range[0], tier_range[1]),
                    locale=Tier.Locale(phrases=tier_phrases_by_lang),
                )
            )

        return tier_objects

    def _build_category_locale(self) -> PlayableCategory.Locale:
        from commands.play.play import PlayableCategory

        assert self._locale_spec is not None

        locale_names = {}
        locale_units = {}

        for lang_code, data in self._locale_spec.items():
            locale_names[lang_code] = data.get("name", "")
            locale_units[lang_code] = data.get("units", "")

        return PlayableCategory.Locale(name=locale_names, units=locale_units)

    def _extract_win_type(self) -> str:
        if isinstance(self._win_value_spec, str):
            return self._win_value_spec
        elif isinstance(self._win_value_spec, tuple):
            return self._win_value_spec[0]
        return "unknown"


def create_category(
    name: str,
    tiers_num: int,
    ranges: Union[Callable[[int], Tuple[int, int]], Dict[int, Tuple[int, int]]],
    phrases: Dict[str, Dict[int, List[str]]],
    win_value: Union[str, Tuple[str, int]],
    locale: Dict[str, Dict[str, str]],
    win_locale: Optional[Dict[str, List[str]]] = None,
    continuous: bool = True,
) -> Optional[PlayableCategory]:
    from commands.play.play_schema import log_schema_errors, validate_full_schema

    validation = validate_full_schema(
        name=name,
        tiers_num=tiers_num,
        ranges=ranges,
        phrases=phrases,
        win_value=win_value,
        locale=locale,
        win_locale=win_locale,
    )

    if validation.has_errors:
        log_schema_errors(name, validation)
        return None

    try:
        builder = (
            PlayableCategoryBuilder(name)
            .with_tiers(tiers_num, ranges)
            .with_phrases(phrases)
            .with_win_value(win_value)
            .with_locale(locale)
            .with_win_locale(win_locale)
            .is_continuous(continuous)
        )

        category = builder.build()

    except ValueError as e:
        logger.critical(
            f"CRITICAL: Category '{name}' failed post-init validation!\n"
            f"Error: {e}\n"
            f"SKIPPING CATEGORY '{name}'"
        )
        return None

    except Exception as e:
        logger.critical(
            f"CRITICAL: Component building failed for '{name}': {e}\n"
            f"SKIPPING CATEGORY '{name}'"
        )
        return None

    return category


def create_all_categories(
    category_specs: List[Dict],
) -> Tuple[List[PlayableCategory], List[CategoryBuildResult]]:
    from commands.play.play_schema import log_schema_errors, validate_full_schema

    results: List[CategoryBuildResult] = []
    schema_valid_specs: List[Dict] = []

    logger.info("=" * 80)
    logger.info("Validating schemas...")
    logger.info("=" * 80)

    for spec in category_specs:
        name = spec["name"]
        validation = validate_full_schema(
            name=name,
            tiers_num=spec["tiers_num"],
            ranges=spec["ranges"],
            phrases=spec["phrases"],
            win_value=spec["win_value"],
            locale=spec["locale"],
            win_locale=spec.get("win_locale"),
        )

        if validation.has_errors:
            log_schema_errors(name, validation)
            results.append(
                CategoryBuildResult(
                    name=name,
                    category=None,
                    phase_failed="schema",
                    errors=validation.all_errors,
                )
            )
        else:
            schema_valid_specs.append(spec)

    logger.info("=" * 80)
    logger.info(f"Building {len(schema_valid_specs)} categories...")
    logger.info("=" * 80)

    successful_categories = []

    for spec in schema_valid_specs:
        name = spec["name"]

        try:
            builder = (
                PlayableCategoryBuilder(name)
                .with_tiers(spec["tiers_num"], spec["ranges"])
                .with_phrases(spec["phrases"])
                .with_win_value(spec["win_value"])
                .with_locale(spec["locale"])
                .with_win_locale(spec.get("win_locale"))
                .is_continuous(spec.get("continuous", True))
            )

            category = builder.build()

            successful_categories.append(category)
            results.append(
                CategoryBuildResult(
                    name=name, category=category, phase_failed=None, errors=[]
                )
            )
            logger.info(f"Successfully created category '{name}'")

        except ValueError as e:
            error_msg = f"Post-init validation failed: {e}"
            logger.critical(f"Category '{name}': {error_msg}")
            results.append(
                CategoryBuildResult(
                    name=name, category=None, phase_failed="post_init", errors=[str(e)]
                )
            )

        except Exception as e:
            error_msg = f"Component building failed: {e}"
            logger.critical(f"Category '{name}': {error_msg}")
            results.append(
                CategoryBuildResult(
                    name=name, category=None, phase_failed="build", errors=[str(e)]
                )
            )

    failed_results = [r for r in results if r.category is None]

    logger.info("=" * 80)
    logger.info("CATEGORY CREATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total categories attempted: {len(category_specs)}")
    logger.info(f"Successful: {len(successful_categories)}")
    logger.info(f"Failed: {len(failed_results)}")

    if failed_results:
        logger.info("\nFailed categories:")
        for result in failed_results:
            logger.info(f"{result.name} (failed at {result.phase_failed} phase)")

    logger.info("=" * 80)

    return successful_categories, failed_results

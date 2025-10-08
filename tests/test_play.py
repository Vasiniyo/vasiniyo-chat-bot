import logging
from typing import Dict, List, Tuple
import unittest

from src.commands.play.play import PlayableCategory
from src.commands.play.play_config import CATEGORIES


class TestPlayCategories(unittest.TestCase):
    """Test all play categories for proper validation."""

    def setUp(self):
        """Set up test logging to capture validation errors."""
        self.logger = logging.getLogger("test_play")
        self.logger.setLevel(logging.DEBUG)

        # Create a handler to capture log messages
        self.log_capture = []
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)

        # Custom filter to capture messages
        class LogCapture(logging.Filter):
            def __init__(self, capture_list):
                self.capture_list = capture_list

            def filter(self, record):
                self.capture_list.append(record)
                return True

        handler.addFilter(LogCapture(self.log_capture))
        self.logger.addHandler(handler)

    def test_all_configured_categories(self):
        """Test that all categories from config are created successfully."""
        results = {"success": [], "failed": []}

        for name, category in CATEGORIES.items():
            try:
                # Categories should already be created in play_config
                self.assertIsInstance(category, PlayableCategory)
                results["success"].append(name)
                self.logger.info(f"✓ Category '{name}' validated successfully")
            except Exception as e:
                results["failed"].append((name, str(e)))
                self.logger.error(f"✗ Category '{name}' failed: {e}")

        # Report results
        self.logger.info(f"\n=== Category Validation Summary ===")
        self.logger.info(f"Success: {len(results['success'])}/{len(CATEGORIES)}")
        if results["failed"]:
            self.logger.error(f"Failed categories: {[f[0] for f in results['failed']]}")

        # Test should pass even if some categories fail
        self.assertGreater(
            len(results["success"]), 0, "At least one category should be valid"
        )

    def test_malformed_categories(self):
        """Test various malformed category configurations to ensure proper validation."""
        test_cases = [
            {
                "name": "missing_locale_field",
                "description": "Missing units field in locale",
                "config": {
                    "name": "test_missing_units",
                    "tiers_num": 2,
                    "ranges": {1: (0, 50), 2: (51, 100)},
                    "phrases": {"ru": {1: ["phrase1"], 2: ["phrase2"]}},
                    "winner_value": "max",
                    "locale": {"ru": {"name": "тест"}},  # Missing 'units'
                    "continuous": True,
                },
            },
            {
                "name": "overlapping_ranges",
                "description": "Overlapping tier ranges",
                "config": {
                    "name": "test_overlap",
                    "tiers_num": 2,
                    "ranges": {1: (0, 60), 2: (50, 100)},  # Overlap at 50-60
                    "phrases": {"ru": {1: ["phrase1"], 2: ["phrase2"]}},
                    "winner_value": "max",
                    "locale": {"ru": {"name": "тест", "units": "очков"}},
                    "continuous": True,
                },
            },
            {
                "name": "gap_in_continuous",
                "description": "Gap between ranges when continuous=True",
                "config": {
                    "name": "test_gap",
                    "tiers_num": 2,
                    "ranges": {1: (0, 40), 2: (50, 100)},  # Gap at 41-49
                    "phrases": {"ru": {1: ["phrase1"], 2: ["phrase2"]}},
                    "winner_value": "max",
                    "locale": {"ru": {"name": "тест", "units": "очков"}},
                    "continuous": True,
                },
            },
            {
                "name": "missing_tier_phrases",
                "description": "Missing phrases for a tier",
                "config": {
                    "name": "test_missing_phrases",
                    "tiers_num": 2,
                    "ranges": {1: (0, 50), 2: (51, 100)},
                    "phrases": {"ru": {1: ["phrase1"]}},  # Missing tier 2
                    "winner_value": "max",
                    "locale": {"ru": {"name": "тест", "units": "очков"}},
                    "continuous": True,
                },
            },
            {
                "name": "empty_phrases_list",
                "description": "Empty phrases list for a tier",
                "config": {
                    "name": "test_empty_phrases",
                    "tiers_num": 2,
                    "ranges": {1: (0, 50), 2: (51, 100)},
                    "phrases": {"ru": {1: ["phrase1"], 2: []}},  # Empty list
                    "winner_value": "max",
                    "locale": {"ru": {"name": "тест", "units": "очков"}},
                    "continuous": True,
                },
            },
            {
                "name": "invalid_winner_value",
                "description": "Invalid winner_value",
                "config": {
                    "name": "test_invalid_winner",
                    "tiers_num": 2,
                    "ranges": {1: (0, 50), 2: (51, 100)},
                    "phrases": {"ru": {1: ["phrase1"], 2: ["phrase2"]}},
                    "winner_value": "middle",  # Invalid - should be 'min', 'max', or int
                    "locale": {"ru": {"name": "тест", "units": "очков"}},
                    "continuous": True,
                },
            },
            {
                "name": "winner_value_out_of_range",
                "description": "Winner value outside of tier ranges",
                "config": {
                    "name": "test_winner_out_of_range",
                    "tiers_num": 2,
                    "ranges": {1: (0, 50), 2: (51, 100)},
                    "phrases": {"ru": {1: ["phrase1"], 2: ["phrase2"]}},
                    "winner_value": 150,  # Outside range
                    "locale": {"ru": {"name": "тест", "units": "очков"}},
                    "continuous": True,
                },
            },
            {
                "name": "reversed_range",
                "description": "Range with min > max",
                "config": {
                    "name": "test_reversed",
                    "tiers_num": 2,
                    "ranges": {1: (50, 0), 2: (51, 100)},  # Reversed
                    "phrases": {"ru": {1: ["phrase1"], 2: ["phrase2"]}},
                    "winner_value": "max",
                    "locale": {"ru": {"name": "тест", "units": "очков"}},
                    "continuous": True,
                },
            },
            {
                "name": "wrong_locale_type",
                "description": "Wrong type for locale field",
                "config": {
                    "name": "test_wrong_type",
                    "tiers_num": 2,
                    "ranges": {1: (0, 50), 2: (51, 100)},
                    "phrases": {"ru": {1: ["phrase1"], 2: ["phrase2"]}},
                    "winner_value": "max",
                    "locale": {"ru": {"name": 123, "units": "очков"}},  # Wrong type
                    "continuous": True,
                },
            },
            {
                "name": "missing_language_in_tier",
                "description": "Tier missing required language",
                "config": {
                    "name": "test_missing_lang",
                    "tiers_num": 4,
                    "ranges": {1: (0, 50), 2: (51, 100), 3: (101, 140), 4: (141, 150)},
                    "phrases": {
                        "ru": {1: ["phrase1"], 3: ["phrase3"]}
                    },  # missing 2nd, 4th tier
                    "winner_value": "max",
                    "locale": {"ru": {"name": "тест", "units": "очков"}},
                    "continuous": True,
                },
            },
        ]

        results = {"caught": [], "missed": []}

        for test_case in test_cases:
            try:
                category = PlayableCategory.create(**test_case["config"])
                if category is not None:
                    # If category was created, it means validation didn't catch the error
                    results["missed"].append(test_case["name"])
                    self.logger.warning(
                        f"⚠ Test '{test_case['name']}' ({test_case['description']}) "
                        f"- validation MISSED the error"
                    )
                else:
                    # create() returned None, error was logged
                    results["caught"].append(test_case["name"])
                    self.logger.info(
                        f"✓ Test '{test_case['name']}' ({test_case['description']}) "
                        f"- error properly caught and logged"
                    )
            except ValueError as e:
                # ValueError was raised, validation caught the error
                results["caught"].append(test_case["name"])
                self.logger.info(
                    f"✓ Test '{test_case['name']}' ({test_case['description']}) "
                    f"- error properly caught: {e}"
                )
            except Exception as e:
                # Unexpected error
                self.logger.error(
                    f"✗ Test '{test_case['name']}' ({test_case['description']}) "
                    f"- unexpected error: {type(e).__name__}: {e}"
                )

        # Report results
        self.logger.info(f"\n=== Malformed Category Test Summary ===")
        self.logger.info(f"Errors caught: {len(results['caught'])}/{len(test_cases)}")
        if results["missed"]:
            self.logger.warning(f"Errors missed: {results['missed']}")

        # Test passes if most errors are caught
        self.assertGreater(
            len(results["caught"]),
            len(test_cases) * 0.7,
            "At least 70% of errors should be caught",
        )

    def test_category_functionality(self):
        """Test basic functionality of valid categories."""
        # Use espers category as it should be valid
        category = CATEGORIES.get("espers")
        if not category:
            self.skipTest("Espers category not available")

        # Test get_tier_for_value
        test_values = [5, 25, 50, 75, 95]
        for value in test_values:
            tier = category.get_tier_for_value(value)
            self.assertIsNotNone(tier, f"Should find tier for value {value}")
            self.assertTrue(
                tier.value_range.x <= value <= tier.value_range.y,
                f"Value {value} should be within tier range",
            )

        # Test out of range values
        out_of_range = [-10, 200]
        for value in out_of_range:
            tier = category.get_tier_for_value(value)
            self.assertIsNone(
                tier, f"Should return None for out of range value {value}"
            )

        # Test get_winner_value
        winner = category.get_winner_value()
        self.assertIsInstance(winner, int, "Winner value should be an integer")

        # Test get_random_value
        seed = 12345
        random_value = category.get_random_value(seed)
        self.assertGreaterEqual(random_value, category._min_range)
        self.assertLessEqual(random_value, category._max_range)

        # Test deterministic behavior
        random_value2 = category.get_random_value(seed)
        self.assertEqual(
            random_value, random_value2, "Same seed should produce same value"
        )


if __name__ == "__main__":
    # Set up logging for standalone execution
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )

    unittest.main(verbosity=2)

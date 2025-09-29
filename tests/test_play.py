from src.commands.play.play import Pair, PlayableCategory, Tier

# Method 1: Using a lambda function
# This creates ranges: (1,2), (3,4), (5,6), (7,8), (9,10)
espers_lambda = PlayableCategory.create(
    name="Espers",
    tiers_num=5,
    ranges=lambda x: (2 * x - 1, 2 * x),
    phrases={i: [f"Esper Tier {i}"] for i in range(1, 6)},
)

# Method 2: Using a dictionary
ranges_dict = {1: (3, 4), 2: (1, 2), 3: (5, 6), 4: (7, 8), 5: (9, 10)}

espers_dict = PlayableCategory.create(
    name="Espers",
    tiers_num=5,
    ranges=ranges_dict,
    phrases={i: [f"Esper Tier {i}"] for i in range(1, 6)},
)

# Method 3: Non-continuous ranges (with gaps)
espers_with_gaps = PlayableCategory.create(
    name="Espers",
    tiers_num=3,
    ranges=lambda x: (x * 5, x * 5 + 2),  # (5,7), (10,12), (15,17) - has gaps
    phrases={i: [f"Esper Rank {i}"] for i in range(1, 4)},
    continuous=False,  # Important: set to False to allow gaps
)


# Test the categories
def test_category(category, test_values):
    print(f"\n=== Testing {category.name} ===")
    print(category)
    print("\nTesting values:")
    for value in test_values:
        tier = category.get_tier_for_value(value)
        if tier:
            idx = category.tiers.index(tier)
            print(f"  Value {value} -> Tier {idx}: {tier.phrases[0]}")
        else:
            print(f"  Value {value} -> No tier found")


# Run tests
if __name__ == "__main__":
    # Test the lambda-based category
    test_category(espers_lambda, [1, 2, 3, 5, 9, 10, 11])

    # Test the dictionary-based category
    test_category(espers_dict, [1, 2, 3, 5, 9, 10, 11])

    # Test non-continuous ranges
    test_category(espers_with_gaps, [5, 7, 8, 10, 12, 13, 15, 17, 20])

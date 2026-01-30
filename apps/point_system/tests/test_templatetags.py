"""Comprehensive tests for point_system template tags."""

from apps.point_system.templatetags.custom_tags import get_item, negativity_class, positivity_class


class TestGetItemFilter:
    """Tests for get_item template filter."""

    def test_existing_key(self):
        """Test getting existing key from dictionary."""
        d = {"a": 1, "b": 2}
        assert get_item(d, "a") == 1
        assert get_item(d, "b") == 2

    def test_missing_key(self):
        """Test getting missing key returns 0."""
        d = {"a": 1}
        assert get_item(d, "missing") == 0

    def test_none_dictionary(self):
        """Test None dictionary returns 0."""
        assert get_item(None, "any") == 0

    def test_empty_dictionary(self):
        """Test empty dictionary returns 0 for any key."""
        d = {}
        assert get_item(d, "any") == 0

    def test_numeric_value(self):
        """Test getting numeric value."""
        d = {"count": 42}
        assert get_item(d, "count") == 42

    def test_string_value(self):
        """Test getting string value."""
        d = {"name": "Alice"}
        assert get_item(d, "name") == "Alice"

    def test_nested_dict_not_supported(self):
        """Test that nested access doesn't work (returns dict)."""
        d = {"outer": {"inner": 1}}
        result = get_item(d, "outer")
        assert result == {"inner": 1}

    def test_list_value(self):
        """Test getting list value."""
        d = {"items": [1, 2, 3]}
        assert get_item(d, "items") == [1, 2, 3]

    def test_none_value(self):
        """Test getting None value."""
        d = {"key": None}
        assert get_item(d, "key") is None

    def test_zero_value(self):
        """Test getting zero value (not confused with default)."""
        d = {"zero": 0}
        assert get_item(d, "zero") == 0

    def test_empty_string_key(self):
        """Test getting empty string key."""
        d = {"": "empty key"}
        assert get_item(d, "") == "empty key"

    def test_numeric_key(self):
        """Test getting numeric key (as string)."""
        d = {1: "one", "1": "string one"}
        assert get_item(d, 1) == "one"
        assert get_item(d, "1") == "string one"


class TestNegativityClassFilter:
    """Tests for negativity_class template filter."""

    def test_level_black_0(self):
        """Test value 0 returns level-black."""
        assert negativity_class(0) == "level-black"

    def test_level_black_1_to_4(self):
        """Test values 1-4 return level-black."""
        for val in [1, 2, 3, 4]:
            assert negativity_class(val) == "level-black"

    def test_level_orange_5(self):
        """Test value 5 returns level-orange."""
        assert negativity_class(5) == "level-orange"

    def test_level_orange_6_to_9(self):
        """Test values 6-9 return level-orange."""
        for val in [6, 7, 8, 9]:
            assert negativity_class(val) == "level-orange"

    def test_level_red_10(self):
        """Test value 10 returns level-red."""
        assert negativity_class(10) == "level-red"

    def test_level_red_11_to_19(self):
        """Test values 11-19 return level-red."""
        for val in [11, 15, 19]:
            assert negativity_class(val) == "level-red"

    def test_level_red_dark_20(self):
        """Test value 20 returns level-red-dark."""
        assert negativity_class(20) == "level-red-dark"

    def test_level_red_dark_above_20(self):
        """Test values above 20 return level-red-dark."""
        for val in [21, 50, 100, 1000]:
            assert negativity_class(val) == "level-red-dark"

    def test_negative_value(self):
        """Test negative value returns level-unknown."""
        assert negativity_class(-1) == "level-unknown"
        assert negativity_class(-10) == "level-unknown"

    def test_string_number(self):
        """Test string number is converted."""
        assert negativity_class("5") == "level-orange"
        assert negativity_class("15") == "level-red"

    def test_invalid_string(self):
        """Test invalid string returns level-unknown."""
        assert negativity_class("abc") == "level-unknown"
        assert negativity_class("") == "level-unknown"

    def test_none_value(self):
        """Test None value returns level-unknown."""
        assert negativity_class(None) == "level-unknown"

    def test_float_value(self):
        """Test float value is converted to int."""
        assert negativity_class(5.9) == "level-orange"  # int(5.9) = 5

    def test_boundary_values(self):
        """Test exact boundary values."""
        assert negativity_class(4) == "level-black"
        assert negativity_class(5) == "level-orange"
        assert negativity_class(9) == "level-orange"
        assert negativity_class(10) == "level-red"
        assert negativity_class(19) == "level-red"
        assert negativity_class(20) == "level-red-dark"


class TestPositivityClassFilter:
    """Tests for positivity_class template filter."""

    def test_level_green_5_and_above(self):
        """Test values 5 and above return level-green."""
        for val in [5, 6, 10, 50, 100]:
            assert positivity_class(val) == "level-green"

    def test_below_5_returns_value(self):
        """Test values below 5 return the value itself (potential bug)."""
        # Note: This appears to be a bug in the filter
        # It returns the numeric value instead of a class name
        assert positivity_class(0) == 0
        assert positivity_class(1) == 1
        assert positivity_class(4) == 4

    def test_string_number(self):
        """Test string number is converted."""
        assert positivity_class("5") == "level-green"
        assert positivity_class("10") == "level-green"

    def test_invalid_string(self):
        """Test invalid string returns level-unknown."""
        assert positivity_class("abc") == "level-unknown"

    def test_none_value(self):
        """Test None value returns level-unknown."""
        assert positivity_class(None) == "level-unknown"

    def test_negative_value(self):
        """Test negative value returns the value (potential bug)."""
        # The filter doesn't handle negative values specially
        assert positivity_class(-1) == -1

    def test_boundary_value_4(self):
        """Test boundary value 4."""
        assert positivity_class(4) == 4  # Returns value, not class

    def test_boundary_value_5(self):
        """Test boundary value 5."""
        assert positivity_class(5) == "level-green"


class TestTemplateTagIntegration:
    """Integration tests for template tags used together."""

    def test_get_item_with_negativity_class(self):
        """Test using get_item result with negativity_class."""
        data = {"tardiness": 15}
        value = get_item(data, "tardiness")
        assert negativity_class(value) == "level-red"

    def test_get_item_with_positivity_class(self):
        """Test using get_item result with positivity_class."""
        data = {"homework": 10}
        value = get_item(data, "homework")
        assert positivity_class(value) == "level-green"

    def test_get_item_missing_with_negativity_class(self):
        """Test missing key (returns 0) with negativity_class."""
        data = {}
        value = get_item(data, "missing")  # Returns 0
        assert negativity_class(value) == "level-black"

    def test_get_item_missing_with_positivity_class(self):
        """Test missing key (returns 0) with positivity_class."""
        data = {}
        value = get_item(data, "missing")  # Returns 0
        assert positivity_class(value) == 0  # Returns value, not class

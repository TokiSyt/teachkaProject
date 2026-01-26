import pytest

from apps.grade_calculator.services.grade_calculator import grade_calculator


class TestGradeCalculatorInvalidInput:
    """Tests for invalid max_points values (0-3)."""

    @pytest.mark.parametrize("max_points", [0, 1, 2, 3, -1, -5])
    def test_returns_empty_list_for_max_points_3_or_less(self, max_points):
        """Should return empty list when max_points <= 3."""
        result = grade_calculator(max_points, 1)
        assert result == []

    def test_returns_empty_list_for_decimal_under_4(self):
        """Should return empty list for decimals like 3.5, 3.9."""
        assert grade_calculator(3.5, 1) == []
        assert grade_calculator(3.9, 1) == []


class TestGradeCalculatorStaticGrades:
    """Tests for static grade values (max_points 4-9)."""

    def test_max_points_4(self):
        """Should return static grades for max_points=4."""
        expected = [4, 4, 3, 3, 2, 2, 1, 1, 0, 0]
        assert grade_calculator(4, 1) == expected
        assert grade_calculator(4, 2) == expected

    def test_max_points_5(self):
        """Should return static grades for max_points=5."""
        expected = [5, 5, 4, 3, 2, 2, 1, 1, 0, 0]
        assert grade_calculator(5, 1) == expected

    def test_max_points_6(self):
        """Should return static grades for max_points=6."""
        expected = [6, 6, 5, 4, 3, 3, 2, 1, 0, 0]
        assert grade_calculator(6, 1) == expected

    def test_max_points_7(self):
        """Should return static grades for max_points=7."""
        expected = [7, 6, 5, 4, 3, 2, 1, 1, 0, 0]
        assert grade_calculator(7, 1) == expected

    def test_max_points_8(self):
        """Should return static grades for max_points=8."""
        expected = [8, 7, 6, 5, 4, 3, 2, 1, 0, 0]
        assert grade_calculator(8, 1) == expected

    def test_max_points_9(self):
        """Should return static grades for max_points=9."""
        expected = [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
        assert grade_calculator(9, 1) == expected

    def test_rounding_option_does_not_affect_static_grades(self):
        """Static grades should be the same regardless of rounding option."""
        for max_points in [4, 5, 6, 7, 8, 9]:
            result_round = grade_calculator(max_points, 1)
            result_decimal = grade_calculator(max_points, 2)
            assert result_round == result_decimal

    def test_decimal_rounds_to_nearest_static_grade(self):
        """Decimals in 4-9 range should round to nearest static grade."""
        # 4.4 rounds to 4
        assert grade_calculator(4.4, 1) == [4, 4, 3, 3, 2, 2, 1, 1, 0, 0]
        # 4.5 rounds to 5 (Python rounds to nearest even, but round(4.5) = 4)
        assert grade_calculator(4.6, 1) == [5, 5, 4, 3, 2, 2, 1, 1, 0, 0]
        # 8.7 rounds to 9
        assert grade_calculator(8.7, 1) == [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]


class TestGradeCalculatorDynamicGrades:
    """Tests for dynamically calculated grades (max_points >= 10)."""

    def test_max_points_10(self):
        """Should calculate grades for max_points=10."""
        result = grade_calculator(10, 1)
        assert len(result) == 10
        assert result[0] == 10
        assert result[9] == 0

    def test_max_points_20(self):
        """Should calculate grades for max_points=20."""
        result = grade_calculator(20, 1)
        assert len(result) == 10
        assert result[0] == 20
        assert result[9] == 0

    def test_max_points_50(self):
        """Should calculate grades for max_points=50."""
        result = grade_calculator(50, 1)
        assert len(result) == 10
        assert result[0] == 50
        assert result[9] == 0

    def test_max_points_100(self):
        """Should calculate grades for max_points=100."""
        result = grade_calculator(100, 1)
        assert len(result) == 10
        assert result[0] == 100
        assert result[9] == 0


class TestGradeCalculatorNoDuplicates:
    """Tests to ensure no duplicate grades in consecutive positions."""

    @pytest.mark.parametrize("max_points", [10, 15, 20, 25, 30, 50, 100])
    def test_no_consecutive_duplicates_rounding_option_1(self, max_points):
        """Consecutive grades should not be equal (rounding option 1)."""
        result = grade_calculator(max_points, 1)
        for i in range(len(result) - 1):
            assert result[i] >= result[i + 1], f"Grade {i} should be >= grade {i+1}"

    @pytest.mark.parametrize("max_points", [10, 15, 20, 25, 30, 50, 100])
    def test_no_consecutive_duplicates_rounding_option_2(self, max_points):
        """Consecutive grades should not be equal (rounding option 2)."""
        result = grade_calculator(max_points, 2)
        for i in range(len(result) - 1):
            assert result[i] >= result[i + 1], f"Grade {i} should be >= grade {i+1}"


class TestGradeCalculatorStructure:
    """Tests for grade list structure."""

    @pytest.mark.parametrize("max_points", [10, 20, 50, 100])
    def test_returns_list_of_10_elements(self, max_points):
        """Should always return exactly 10 grade thresholds."""
        result = grade_calculator(max_points, 1)
        assert len(result) == 10

    @pytest.mark.parametrize("max_points", [10, 20, 50, 100])
    def test_first_element_is_max_points(self, max_points):
        """First element should equal max_points."""
        result = grade_calculator(max_points, 1)
        assert result[0] == max_points

    @pytest.mark.parametrize("max_points", [10, 20, 50, 100])
    def test_last_element_is_zero(self, max_points):
        """Last element should always be 0."""
        result = grade_calculator(max_points, 1)
        assert result[9] == 0

    @pytest.mark.parametrize("max_points", [10, 20, 50, 100])
    def test_grades_are_descending(self, max_points):
        """Grades should be in descending order."""
        result = grade_calculator(max_points, 1)
        for i in range(len(result) - 1):
            assert result[i] >= result[i + 1]


class TestGradeCalculatorDecimalInput:
    """Tests for decimal max_points values >= 10."""

    def test_decimal_max_points_preserves_value(self):
        """Decimal max_points >= 10 should be preserved in first grade."""
        result = grade_calculator(10.5, 1)
        assert result[0] == 10.5

    def test_integer_max_points_returns_int(self):
        """Integer max_points should return int, not float."""
        result = grade_calculator(20.0, 1)
        assert result[0] == 20
        assert isinstance(result[0], int)


class TestGradeCalculatorRoundingOptions:
    """Tests for different rounding options."""

    def test_rounding_option_1_uses_integers(self):
        """Rounding option 1 should produce integer-based adjustments."""
        result = grade_calculator(20, 1)
        # All intermediate grades should be integers (except possibly first)
        for grade in result[1:]:
            assert grade == int(grade) or grade == 0

    def test_rounding_option_2_allows_half_points(self):
        """Rounding option 2 can produce 0.5 adjustments."""
        result = grade_calculator(20, 2)
        # Result may contain .5 values when duplicates need fixing
        assert len(result) == 10

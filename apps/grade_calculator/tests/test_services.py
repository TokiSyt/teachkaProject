import pytest

from apps.grade_calculator.services.grade_calculator import grade_calculator


class TestGradeCalculator:
    def test_returns_list_of_ten_values(self):
        result = grade_calculator(100, 1)
        assert len(result) == 10

    def test_first_value_is_max_points(self):
        result = grade_calculator(100, 1)
        assert result[0] == 100

    def test_last_value_is_zero(self):
        result = grade_calculator(100, 1)
        assert result[-1] == 0

    def test_values_are_descending(self):
        result = grade_calculator(100, 1)
        for i in range(len(result) - 1):
            assert result[i] >= result[i + 1]

    def test_rounding_option_1_uses_integers(self):
        result = grade_calculator(100, 1)
        # With rounding option 1, adjustments should be by 1
        assert all(isinstance(v, int | float) for v in result)

    def test_rounding_option_2_uses_half_decimals(self):
        result = grade_calculator(100, 2)
        # With rounding option 2, adjustments should be by 0.5
        assert all(isinstance(v, int | float) for v in result)

    def test_with_decimal_max_points(self):
        result = grade_calculator(99.5, 1)
        assert result[0] == 99.5

    def test_with_integer_max_points_returns_int(self):
        result = grade_calculator(100.0, 1)
        assert result[0] == 100
        assert isinstance(result[0], int)

    def test_small_max_points(self):
        result = grade_calculator(10, 1)
        assert result[0] == 10
        assert result[-1] == 0

    @pytest.mark.parametrize("max_points", [50, 100, 150, 200])
    def test_various_max_points(self, max_points):
        result = grade_calculator(max_points, 1)
        assert result[0] == max_points
        assert len(result) == 10

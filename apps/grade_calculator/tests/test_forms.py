from apps.grade_calculator.forms import GradeCalculatorForm


class TestGradeCalculatorForm:
    def test_valid_data(self):
        form = GradeCalculatorForm(data={"max_points": 100, "rounding_option": 1})
        assert form.is_valid()

    def test_valid_decimal_max_points(self):
        form = GradeCalculatorForm(data={"max_points": 99.5, "rounding_option": 1})
        assert form.is_valid()

    def test_rounding_option_2_is_valid(self):
        form = GradeCalculatorForm(data={"max_points": 100, "rounding_option": 2})
        assert form.is_valid()

    def test_negative_max_points_invalid(self):
        form = GradeCalculatorForm(data={"max_points": -10, "rounding_option": 1})
        assert not form.is_valid()
        assert "max_points" in form.errors

    def test_missing_max_points_invalid(self):
        form = GradeCalculatorForm(data={"rounding_option": 1})
        assert not form.is_valid()
        assert "max_points" in form.errors

    def test_missing_rounding_option_invalid(self):
        form = GradeCalculatorForm(data={"max_points": 100})
        assert not form.is_valid()
        assert "rounding_option" in form.errors

    def test_rounding_option_coerced_to_int(self):
        form = GradeCalculatorForm(data={"max_points": 100, "rounding_option": "1"})
        assert form.is_valid()
        assert form.cleaned_data["rounding_option"] == 1
        assert isinstance(form.cleaned_data["rounding_option"], int)

from apps.wheel.forms import NameWheelForm


class TestNameWheelForm:
    """Tests for NameWheelForm."""

    def test_valid_form(self):
        """Form is valid with valid data."""
        form = NameWheelForm(data={"members_chosen": 1})
        assert form.is_valid()

    def test_valid_form_multiple_members(self):
        """Form is valid with multiple members chosen."""
        form = NameWheelForm(data={"members_chosen": 5})
        assert form.is_valid()

    def test_invalid_form_zero_members(self):
        """Form is invalid with 0 members chosen."""
        form = NameWheelForm(data={"members_chosen": 0})
        assert not form.is_valid()
        assert "members_chosen" in form.errors

    def test_invalid_form_negative_members(self):
        """Form is invalid with negative members chosen."""
        form = NameWheelForm(data={"members_chosen": -1})
        assert not form.is_valid()
        assert "members_chosen" in form.errors

    def test_invalid_form_missing_members_chosen(self):
        """Form is invalid without members_chosen."""
        form = NameWheelForm(data={})
        assert not form.is_valid()
        assert "members_chosen" in form.errors

    def test_default_initial_value(self):
        """Form has default initial value of 1."""
        form = NameWheelForm()
        assert form.fields["members_chosen"].initial == 1

    def test_min_value_is_one(self):
        """Form enforces minimum value of 1."""
        form = NameWheelForm(data={"members_chosen": 1})
        assert form.is_valid()
        assert form.fields["members_chosen"].min_value == 1

    def test_large_value_is_valid(self):
        """Large values are technically valid (view handles max)."""
        form = NameWheelForm(data={"members_chosen": 1000})
        assert form.is_valid()

    def test_non_integer_is_invalid(self):
        """Non-integer values are invalid."""
        form = NameWheelForm(data={"members_chosen": "abc"})
        assert not form.is_valid()
        assert "members_chosen" in form.errors

    def test_float_is_invalid(self):
        """Float values are invalid."""
        form = NameWheelForm(data={"members_chosen": 1.5})
        assert not form.is_valid()
        assert "members_chosen" in form.errors

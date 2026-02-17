from apps.timer.forms import CountdownmForm


class TestCountdownForm:
    """Tests for CountdownmForm."""

    def test_valid_form(self):
        """Form is valid with proper time."""
        form = CountdownmForm(data={"total_time": "01:30:00"})
        assert form.is_valid()

    def test_valid_form_minutes_only(self):
        """Form is valid with minutes and seconds."""
        form = CountdownmForm(data={"total_time": "00:05:00"})
        assert form.is_valid()

    def test_invalid_form_empty(self):
        """Form is invalid without data."""
        form = CountdownmForm(data={})
        assert not form.is_valid()
        assert "total_time" in form.errors

    def test_invalid_form_bad_format(self):
        """Form is invalid with wrong format."""
        form = CountdownmForm(data={"total_time": "abc"})
        assert not form.is_valid()
        assert "total_time" in form.errors

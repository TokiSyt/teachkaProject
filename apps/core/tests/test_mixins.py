"""Tests for core app mixins."""

from apps.core.mixins import UserQuerySetMixin


class TestUserQuerySetMixin:
    """Tests for UserQuerySetMixin."""

    def test_mixin_has_user_field_attribute(self):
        """UserQuerySetMixin should have user_field attribute."""
        assert hasattr(UserQuerySetMixin, "user_field")
        assert UserQuerySetMixin.user_field == "user"

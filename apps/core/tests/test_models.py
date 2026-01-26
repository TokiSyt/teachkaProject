"""Tests for core app models."""

from django.db import models

from apps.core.models import TimestampedModel, UserOwnedModel


class TestTimestampedModel:
    """Tests for TimestampedModel."""

    def test_is_abstract(self):
        """TimestampedModel should be abstract."""
        assert TimestampedModel._meta.abstract is True

    def test_has_created_at_field(self):
        """TimestampedModel should have created_at field."""
        field = TimestampedModel._meta.get_field("created_at")
        assert isinstance(field, models.DateTimeField)
        assert field.auto_now_add is True

    def test_has_updated_at_field(self):
        """TimestampedModel should have updated_at field."""
        field = TimestampedModel._meta.get_field("updated_at")
        assert isinstance(field, models.DateTimeField)
        assert field.auto_now is True


class TestUserOwnedModel:
    """Tests for UserOwnedModel."""

    def test_is_abstract(self):
        """UserOwnedModel should be abstract."""
        assert UserOwnedModel._meta.abstract is True

    def test_inherits_timestamped(self):
        """UserOwnedModel should inherit from TimestampedModel."""
        assert issubclass(UserOwnedModel, TimestampedModel)

    def test_has_user_field(self):
        """UserOwnedModel should have user field."""
        field = UserOwnedModel._meta.get_field("user")
        assert isinstance(field, models.ForeignKey)

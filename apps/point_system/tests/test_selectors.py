"""Tests for point_system app selectors."""

import pytest
from django.http import Http404

from apps.point_system import selectors


@pytest.mark.django_db
class TestSelectors:
    """Tests for point_system selectors."""

    def test_get_user_groups(self, user, group_with_fields):
        """Test getting user's groups."""
        groups = selectors.get_user_groups(user)
        assert group_with_fields in groups

    def test_get_user_groups_excludes_others(self, user, other_user, group_with_fields):
        """Test that selector excludes other users' groups."""
        groups = selectors.get_user_groups(other_user)
        assert group_with_fields not in groups

    def test_get_group_with_members(self, user, group_with_fields):
        """Test getting group with members."""
        group, members = selectors.get_group_with_members(group_with_fields.id, user)
        assert group == group_with_fields
        assert members.count() == 2

    def test_get_group_with_members_permission_denied(self, other_user, group_with_fields):
        """Test that selector raises 404 for unauthorized user."""
        with pytest.raises(Http404):
            selectors.get_group_with_members(group_with_fields.id, other_user)

    def test_get_group_with_fields(self, user, group_with_fields):
        """Test getting group with field definitions."""
        group, fields = selectors.get_group_with_fields(group_with_fields.id, user)
        assert group == group_with_fields
        assert "homework" in fields["positive_names"]
        assert "tardiness" in fields["negative_names"]

    def test_get_group_full_data(self, user, group_with_fields):
        """Test getting complete group data."""
        data = selectors.get_group_full_data(group_with_fields.id, user)

        assert data["group"] == group_with_fields
        assert len(list(data["members"])) == 2
        assert "homework" in data["positive_column_names"]
        assert "tardiness" in data["negative_column_names"]

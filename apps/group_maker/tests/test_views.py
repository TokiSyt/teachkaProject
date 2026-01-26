"""Tests for group_maker app views."""

import pytest

from apps.group_maker.models import GroupCreationModel


@pytest.mark.django_db
class TestGroupHomeView:
    """Tests for GroupHome view."""

    def test_requires_login(self, client):
        """Test that view requires authentication."""
        # Using the URL path directly since namespace may vary
        response = client.get("/groups/")
        assert response.status_code == 302
        assert "/login" in response.url

    def test_shows_user_groups(self, authenticated_client, group):
        """Test that view shows user's groups."""
        response = authenticated_client.get("/groups/")
        assert response.status_code == 200
        assert group.title in response.content.decode()


@pytest.mark.django_db
class TestGroupCreateView:
    """Tests for GroupCreate view."""

    def test_requires_login(self, client):
        """Test that view requires authentication."""
        response = client.get("/groups/group_maker_creation/")
        assert response.status_code == 302

    def test_creates_group(self, authenticated_client, user):
        """Test creating a new group."""
        data = {
            "title": "New Group",
            "members_string": "Member1, Member2",
        }
        response = authenticated_client.post("/groups/group_maker_creation/", data)
        assert response.status_code == 302  # Redirect on success

        group = GroupCreationModel.objects.get(title="New Group")
        assert group.user == user
        assert group.size == 2


@pytest.mark.django_db
class TestGroupDeleteView:
    """Tests for GroupDelete view."""

    def test_requires_login(self, client, group):
        """Test that view requires authentication."""
        response = client.get(f"/groups/group_maker_delete/{group.pk}")
        assert response.status_code == 302

    def test_deletes_group(self, authenticated_client, group):
        """Test deleting a group."""
        response = authenticated_client.post(f"/groups/group_maker_delete/{group.pk}")
        assert response.status_code == 302
        assert not GroupCreationModel.objects.filter(pk=group.pk).exists()

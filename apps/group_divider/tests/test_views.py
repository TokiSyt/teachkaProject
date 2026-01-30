import pytest
from django.urls import reverse

from apps.group_maker.tests.factories import GroupCreationModelFactory


class TestGroupDividerHomeView:
    @pytest.fixture
    def url(self):
        return reverse("group_divider:home")

    @pytest.fixture
    def group(self, user):
        return GroupCreationModelFactory(user=user, members_string="Alice, Bob, Charlie, Dave, Eve, Frank")

    def test_requires_login(self, client, url):
        response = client.get(url)
        assert response.status_code == 302
        assert "/login" in response.url

    def test_get_shows_user_groups(self, authenticated_client, url, group):
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert "groups" in response.context
        assert group in response.context["groups"]

    def test_get_shows_form(self, authenticated_client, url, group):
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert "form" in response.context

    def test_post_splits_group(self, authenticated_client, url, group):
        response = authenticated_client.post(url, {"group_id": group.id, "size": 2})
        assert response.status_code == 200
        assert "splitted_group" in response.context
        assert len(response.context["splitted_group"]) == 3  # 6 members / 2 = 3 groups

    def test_post_with_different_size(self, authenticated_client, url, group):
        response = authenticated_client.post(url, {"group_id": group.id, "size": 3})
        assert response.status_code == 200
        assert "splitted_group" in response.context
        assert len(response.context["splitted_group"]) == 2  # 6 members / 3 = 2 groups

    def test_post_returns_selected_group(self, authenticated_client, url, group):
        response = authenticated_client.post(url, {"group_id": group.id, "size": 2})
        assert response.context["selected_group"] == group

    def test_post_invalid_size_shows_errors(self, authenticated_client, url, group):
        response = authenticated_client.post(url, {"group_id": group.id, "size": 0})
        assert response.status_code == 200
        assert response.context["form"].errors

    def test_post_missing_size_shows_errors(self, authenticated_client, url, group):
        response = authenticated_client.post(url, {"group_id": group.id})
        assert response.status_code == 200
        assert response.context["form"].errors

    def test_other_user_cannot_access_group(self, client, other_user, url, group):
        client.login(username="otheruser", password="otherpass123")
        response = client.post(url, {"group_id": group.id, "size": 2})
        assert response.status_code == 404

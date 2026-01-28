import pytest
from django.urls import reverse

from apps.group_maker.tests.factories import GroupCreationModelFactory


class TestWheelHomeView:
    @pytest.fixture
    def url(self):
        return reverse("wheel:home")

    @pytest.fixture
    def group(self, user):
        return GroupCreationModelFactory(user=user, members_string="Alice, Bob, Charlie")

    def test_requires_login(self, client, url):
        response = client.get(url)
        assert response.status_code == 302
        assert "/login" in response.url

    def test_get_shows_user_groups(self, authenticated_client, url, group):
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert "groups" in response.context
        assert group in response.context["groups"]

    def test_get_with_group_id_selects_group(self, authenticated_client, url, group):
        response = authenticated_client.get(url + f"?group_id={group.id}")
        assert response.status_code == 200
        assert response.context["selected_group"] == group

    def test_get_with_reset_clears_session(self, authenticated_client, url, group):
        session = authenticated_client.session
        session[f"already_chosen_names_{group.id}"] = ["Alice"]
        session.save()

        response = authenticated_client.get(url + "?reset=1")
        assert response.status_code == 200

    def test_post_spins_wheel(self, authenticated_client, url, group):
        response = authenticated_client.post(url, {"group_id": group.id})
        assert response.status_code == 200
        assert "chosen_name" in response.context
        assert response.context["chosen_name"] in ["Alice", "Bob", "Charlie"]

    def test_post_tracks_chosen_names(self, authenticated_client, url, group):
        response = authenticated_client.post(url, {"group_id": group.id})
        assert "already_chosen_names" in response.context
        assert len(response.context["already_chosen_names"]) == 1

    def test_post_all_names_chosen_shows_message(self, authenticated_client, url, group):
        session = authenticated_client.session
        session[f"already_chosen_names_{group.id}"] = ["Alice", "Bob", "Charlie"]
        session.save()

        response = authenticated_client.post(url, {"group_id": group.id})
        assert response.status_code == 200
        assert response.context.get("message") == "All names chosen!"

    def test_post_without_group_id(self, authenticated_client, url):
        response = authenticated_client.post(url, {})
        assert response.status_code == 200

    def test_other_user_cannot_access_group(self, client, other_user, url, group):
        client.login(username="otheruser", password="otherpass123")
        response = client.get(url + f"?group_id={group.id}")
        assert response.status_code == 404

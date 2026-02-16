import json

import pytest
from django.urls import reverse

from apps.group_maker.tests.factories import GroupCreationModelFactory


@pytest.mark.django_db
class TestHomeViewGet:
    """Tests for HomeView GET requests."""

    @pytest.fixture
    def url(self):
        return reverse("wheel:home")

    @pytest.fixture
    def group(self, user):
        return GroupCreationModelFactory(user=user, members_string="Alice, Bob, Charlie")

    def test_requires_login(self, client, url):
        """Unauthenticated users are redirected to login."""
        response = client.get(url)
        assert response.status_code == 302
        assert "/login" in response.url

    def test_get_returns_200(self, authenticated_client, url):
        """Authenticated users can access the page."""
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_get_shows_user_groups(self, authenticated_client, url, group):
        """User's groups are shown in context."""
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert "groups" in response.context
        assert group in response.context["groups"]

    def test_get_does_not_show_other_user_groups(self, authenticated_client, url, other_user):
        """Other user's groups are not shown."""
        other_group = GroupCreationModelFactory(user=other_user, members_string="X, Y, Z")
        response = authenticated_client.get(url)
        assert other_group not in response.context["groups"]

    def test_get_with_group_id_selects_group(self, authenticated_client, url, group):
        """Group is selected when group_id is provided."""
        response = authenticated_client.get(url + f"?group_id={group.id}")
        assert response.status_code == 200
        assert response.context["selected_group"] == group

    def test_get_with_invalid_group_id_returns_404(self, authenticated_client, url):
        """Invalid group_id returns 404."""
        response = authenticated_client.get(url + "?group_id=99999")
        assert response.status_code == 404

    def test_get_with_other_user_group_id_returns_404(self, authenticated_client, url, other_user):
        """Cannot access other user's group."""
        other_group = GroupCreationModelFactory(user=other_user, members_string="X, Y, Z")
        response = authenticated_client.get(url + f"?group_id={other_group.id}")
        assert response.status_code == 404

    def test_get_with_reset_clears_all_session_keys(self, authenticated_client, url, group):
        """Reset clears all already_chosen_members session keys."""
        session = authenticated_client.session
        session[f"already_chosen_members_{group.id}"] = [1, 2]
        session["already_chosen_members_999"] = [3]
        session.save()

        response = authenticated_client.get(url + "?reset=1")
        assert response.status_code == 200

        # Refresh session
        session = authenticated_client.session
        assert f"already_chosen_members_{group.id}" not in session
        assert "already_chosen_members_999" not in session

    def test_get_shows_already_chosen_members(self, authenticated_client, url, group):
        """Already chosen members are shown in context."""
        member_ids = list(group.members.values_list("id", flat=True)[:2])

        session = authenticated_client.session
        session[f"already_chosen_members_{group.id}"] = member_ids
        session.save()

        response = authenticated_client.get(url + f"?group_id={group.id}")
        assert "already_chosen_members" in response.context
        assert response.context["already_chosen_members"].count() == 2

    def test_get_shows_message_from_session(self, authenticated_client, url):
        """Message stored in session is shown."""
        session = authenticated_client.session
        session["wheel_message"] = "Test message"
        session.save()

        response = authenticated_client.get(url)
        assert response.context.get("message") == "Test message"

        # Message should be cleared after display
        session = authenticated_client.session
        assert "wheel_message" not in session

    def test_get_shows_spin_result_from_session(self, authenticated_client, url, group):
        """Spin result from session is shown and cleared."""
        member = group.members.first()

        session = authenticated_client.session
        session[f"spin_result_{group.id}"] = {
            "chosen_member_ids": [member.id],
            "members_chosen": 1,
        }
        session.save()

        response = authenticated_client.get(url + f"?group_id={group.id}")
        assert "chosen_members" in response.context
        assert member in response.context["chosen_members"]

        # Result should be cleared after display
        session = authenticated_client.session
        assert f"spin_result_{group.id}" not in session


@pytest.mark.django_db
class TestHomeViewPostNonAjax:
    """Tests for HomeView POST requests (non-AJAX)."""

    @pytest.fixture
    def url(self):
        return reverse("wheel:home")

    @pytest.fixture
    def group(self, user):
        return GroupCreationModelFactory(user=user, members_string="Alice, Bob, Charlie")

    def test_post_without_group_id_shows_message(self, authenticated_client, url):
        """POST without group_id shows error message."""
        response = authenticated_client.post(url, {})
        assert response.status_code == 200
        assert "Please select a group first" in response.context.get("message", "")

    def test_post_redirects_after_spin(self, authenticated_client, url, group):
        """POST redirects to GET after successful spin."""
        response = authenticated_client.post(
            url,
            {"group_id": group.id, "remove_after_spin": "on"},
            follow=False,
        )
        assert response.status_code == 302
        assert f"group_id={group.id}" in response.url

    def test_post_stores_spin_result_in_session(self, authenticated_client, url, group):
        """Spin result is stored in session for redirect."""
        authenticated_client.post(
            url,
            {"group_id": group.id, "remove_after_spin": "on"},
        )

        session = authenticated_client.session
        spin_result_key = f"spin_result_{group.id}"
        assert spin_result_key in session
        assert "chosen_member_ids" in session[spin_result_key]

    def test_post_tracks_chosen_members_in_session(self, authenticated_client, url, group):
        """Chosen members are tracked in session when remove_after_spin is on."""
        authenticated_client.post(
            url,
            {"group_id": group.id, "remove_after_spin": "on"},
        )

        session = authenticated_client.session
        session_key = f"already_chosen_members_{group.id}"
        assert session_key in session
        assert len(session[session_key]) == 1

    def test_post_does_not_track_when_remove_after_spin_off(self, authenticated_client, url, group):
        """Chosen members are NOT tracked when remove_after_spin is off."""
        authenticated_client.post(
            url,
            {"group_id": group.id},  # remove_after_spin not set
        )

        session = authenticated_client.session
        session_key = f"already_chosen_members_{group.id}"
        # Session key should not exist or be empty
        assert session.get(session_key, []) == []

    def test_post_chooses_multiple_members(self, authenticated_client, url, group):
        """Multiple members can be chosen in one spin."""
        authenticated_client.post(
            url,
            {"group_id": group.id, "members_chosen": 2, "remove_after_spin": "on"},
        )

        session = authenticated_client.session
        spin_result = session.get(f"spin_result_{group.id}", {})
        assert len(spin_result.get("chosen_member_ids", [])) == 2

    def test_post_all_members_chosen_redirects_with_message(self, authenticated_client, url, group):
        """When all members chosen, redirects with message."""
        member_ids = list(group.members.values_list("id", flat=True))

        session = authenticated_client.session
        session[f"already_chosen_members_{group.id}"] = member_ids
        session.save()

        response = authenticated_client.post(
            url,
            {"group_id": group.id, "remove_after_spin": "on"},
            follow=False,
        )
        assert response.status_code == 302

        session = authenticated_client.session
        assert "All members chosen" in session.get("wheel_message", "")

    def test_post_clear_session_resets_chosen_members(self, authenticated_client, url, group):
        """clear_session=1 resets the chosen members for that group."""
        session = authenticated_client.session
        session[f"already_chosen_members_{group.id}"] = [1, 2]
        session.save()

        authenticated_client.post(
            url,
            {"group_id": group.id, "clear_session": "1", "remove_after_spin": "on"},
        )

        # After spin, should have only 1 chosen (not 3)
        session = authenticated_client.session
        assert len(session.get(f"already_chosen_members_{group.id}", [])) == 1

    def test_post_increments_wheel_spins_counter(self, authenticated_client, url, group, user):
        """User's wheel_spins counter is incremented."""
        initial_spins = user.wheel_spins

        authenticated_client.post(
            url,
            {"group_id": group.id, "remove_after_spin": "on"},
        )

        user.refresh_from_db()
        assert user.wheel_spins == initial_spins + 1

    def test_post_cannot_access_other_user_group(self, authenticated_client, url, other_user):
        """Cannot spin wheel for other user's group."""
        other_group = GroupCreationModelFactory(user=other_user, members_string="X, Y, Z")
        response = authenticated_client.post(url, {"group_id": other_group.id})
        assert response.status_code == 404


@pytest.mark.django_db
class TestHomeViewPostAjax:
    """Tests for HomeView POST requests (AJAX)."""

    @pytest.fixture
    def url(self):
        return reverse("wheel:home")

    @pytest.fixture
    def group(self, user):
        return GroupCreationModelFactory(user=user, members_string="Alice, Bob, Charlie")

    def ajax_post(self, client, url, data):
        """Helper to make AJAX POST request."""
        return client.post(
            url,
            data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

    def test_ajax_post_returns_json(self, authenticated_client, url, group):
        """AJAX POST returns JSON response."""
        response = self.ajax_post(
            authenticated_client,
            url,
            {"group_id": group.id, "remove_after_spin": "on"},
        )
        assert response.status_code == 200
        assert response["Content-Type"] == "application/json"

    def test_ajax_post_returns_chosen_members(self, authenticated_client, url, group):
        """AJAX response includes chosen member names and IDs."""
        response = self.ajax_post(
            authenticated_client,
            url,
            {"group_id": group.id, "remove_after_spin": "on"},
        )
        data = json.loads(response.content)
        assert "chosen_members" in data
        assert "chosen_ids" in data
        assert len(data["chosen_members"]) == 1
        assert len(data["chosen_ids"]) == 1
        assert data["chosen_members"][0] in ["Alice", "Bob", "Charlie"]

    def test_ajax_post_returns_already_chosen(self, authenticated_client, url, group):
        """AJAX response includes already chosen member IDs."""
        response = self.ajax_post(
            authenticated_client,
            url,
            {"group_id": group.id, "remove_after_spin": "on"},
        )
        data = json.loads(response.content)
        assert "already_chosen_ids" in data
        assert len(data["already_chosen_ids"]) == 1

    def test_ajax_post_without_group_id_returns_error(self, authenticated_client, url):
        """AJAX POST without group_id returns error JSON."""
        response = self.ajax_post(authenticated_client, url, {})
        assert response.status_code == 400
        data = json.loads(response.content)
        assert "error" in data
        assert "No group selected" in data["error"]

    def test_ajax_post_all_chosen_returns_error(self, authenticated_client, url, group):
        """AJAX POST when all members chosen returns error JSON."""
        member_ids = list(group.members.values_list("id", flat=True))

        session = authenticated_client.session
        session[f"already_chosen_members_{group.id}"] = member_ids
        session.save()

        response = self.ajax_post(
            authenticated_client,
            url,
            {"group_id": group.id, "remove_after_spin": "on"},
        )
        data = json.loads(response.content)
        assert "error" in data
        assert "All members chosen" in data["error"]
        assert data.get("all_chosen") is True

    def test_ajax_post_multiple_members(self, authenticated_client, url, group):
        """AJAX POST can choose multiple members."""
        response = self.ajax_post(
            authenticated_client,
            url,
            {"group_id": group.id, "members_chosen": 2, "remove_after_spin": "on"},
        )
        data = json.loads(response.content)
        assert len(data["chosen_members"]) == 2

    def test_ajax_post_remove_after_spin_off(self, authenticated_client, url, group):
        """AJAX POST with remove_after_spin off doesn't track in session."""
        response = self.ajax_post(
            authenticated_client,
            url,
            {"group_id": group.id},  # remove_after_spin not set
        )
        assert response.status_code == 200

        session = authenticated_client.session
        session_key = f"already_chosen_members_{group.id}"
        assert session.get(session_key, []) == []

    def test_ajax_post_remove_after_spin_off_returns_chosen_in_response(self, authenticated_client, url, group):
        """AJAX POST with remove_after_spin off includes chosen member in response but not session."""
        response = self.ajax_post(
            authenticated_client,
            url,
            {"group_id": group.id},
        )
        data = json.loads(response.content)
        # The response includes the just-chosen member (for JS wheel update)
        # but session is not updated
        assert len(data["already_chosen_ids"]) == 1
        member_ids = list(group.members.values_list("id", flat=True))
        assert data["already_chosen_ids"][0] in member_ids

    def test_ajax_post_increments_wheel_spins(self, authenticated_client, url, group, user):
        """AJAX POST increments wheel_spins counter."""
        initial_spins = user.wheel_spins

        self.ajax_post(
            authenticated_client,
            url,
            {"group_id": group.id, "remove_after_spin": "on"},
        )

        user.refresh_from_db()
        assert user.wheel_spins == initial_spins + 1

    def test_ajax_post_consecutive_spins_track_all(self, authenticated_client, url, group):
        """Multiple AJAX spins track all chosen members."""
        # First spin
        self.ajax_post(
            authenticated_client,
            url,
            {"group_id": group.id, "remove_after_spin": "on"},
        )

        # Second spin
        response = self.ajax_post(
            authenticated_client,
            url,
            {"group_id": group.id, "remove_after_spin": "on"},
        )
        data = json.loads(response.content)
        assert len(data["already_chosen_ids"]) == 2

    def test_ajax_post_cannot_choose_more_than_available(self, authenticated_client, url, group):
        """Requesting more members than available returns only available."""
        response = self.ajax_post(
            authenticated_client,
            url,
            {"group_id": group.id, "members_chosen": 10, "remove_after_spin": "on"},
        )
        data = json.loads(response.content)
        # Group has 3 members, so max 3 can be chosen
        assert len(data["chosen_members"]) == 3


@pytest.mark.django_db
class TestHomeViewEdgeCases:
    """Edge case tests for HomeView."""

    @pytest.fixture
    def url(self):
        return reverse("wheel:home")

    def test_single_member_group(self, authenticated_client, url, user):
        """Single member group works correctly."""
        group = GroupCreationModelFactory(user=user, members_string="OnlyOne")

        response = authenticated_client.post(
            url,
            {"group_id": group.id, "remove_after_spin": "on"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        data = json.loads(response.content)
        assert data["chosen_members"] == ["OnlyOne"]

    def test_group_with_duplicate_names(self, authenticated_client, url, user):
        """Group with duplicate names handles them separately."""
        group = GroupCreationModelFactory(user=user, members_string="John, Alice, John")

        # Spin 3 times - should be able to get all 3
        for _ in range(3):
            response = authenticated_client.post(
                url,
                {"group_id": group.id, "remove_after_spin": "on"},
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
            assert response.status_code == 200

        session = authenticated_client.session
        assert len(session.get(f"already_chosen_members_{group.id}", [])) == 3

    def test_large_members_chosen_value(self, authenticated_client, url, user):
        """Large members_chosen value is handled gracefully."""
        group = GroupCreationModelFactory(user=user, members_string="A, B")

        response = authenticated_client.post(
            url,
            {"group_id": group.id, "members_chosen": 999, "remove_after_spin": "on"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        data = json.loads(response.content)
        # Should only return 2 (all available)
        assert len(data["chosen_members"]) == 2

    def test_members_chosen_default_value(self, authenticated_client, url, user):
        """members_chosen defaults to 1 if not provided."""
        group = GroupCreationModelFactory(user=user, members_string="A, B, C")

        response = authenticated_client.post(
            url,
            {"group_id": group.id, "remove_after_spin": "on"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        data = json.loads(response.content)
        assert len(data["chosen_members"]) == 1

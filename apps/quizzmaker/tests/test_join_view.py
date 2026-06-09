"""JoinView GET behaviour: prefill nickname for authenticated users."""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestJoinNicknamePrefill:
    def test_authenticated_user_gets_username_prefilled(self, authenticated_client, user):
        resp = authenticated_client.get(reverse("quizzmaker:join"))
        assert resp.status_code == 200
        assert resp.context["nickname"] == user.username

    def test_anonymous_user_has_empty_nickname(self, client):
        resp = client.get(reverse("quizzmaker:join"))
        assert resp.status_code == 200
        assert resp.context["nickname"] == ""

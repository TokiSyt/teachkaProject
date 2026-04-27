"""Tests for quiz CRUD views (create/update)."""

import pytest
from django.urls import reverse

from apps.quizzmaker.models import Quiz


@pytest.mark.django_db
class TestQuizCreateView:
    def test_anonymous_redirected_to_login(self, client):
        resp = client.get(reverse("quizzmaker:create"))
        assert resp.status_code == 302
        assert "login" in resp.url.lower()

    def test_authenticated_get_renders_form(self, authenticated_client):
        resp = authenticated_client.get(reverse("quizzmaker:create"))
        assert resp.status_code == 200
        assert "form" in resp.context

    def test_post_creates_quiz_for_user(self, authenticated_client, user):
        resp = authenticated_client.post(
            reverse("quizzmaker:create"),
            data={
                "title": "New Quiz",
                "visibility": Quiz.PUBLIC,
                "focus_x": 50,
                "focus_y": 50,
            },
        )
        assert resp.status_code == 302
        q = Quiz.objects.get(title="New Quiz")
        assert q.user == user
        assert resp.url == reverse("quizzmaker:rounds", kwargs={"pk": q.pk})


@pytest.mark.django_db
class TestQuizUpdateView:
    def _post(self, client, quiz, **fields):
        defaults = {
            "title": quiz.title,
            "visibility": quiz.visibility,
            "focus_x": 50,
            "focus_y": 50,
        }
        defaults.update(fields)
        return client.post(reverse("quizzmaker:edit", kwargs={"pk": quiz.pk}), data=defaults)

    def test_valid_update_changes_title_and_redirects_to_rounds(self, authenticated_client, quiz):
        resp = self._post(authenticated_client, quiz, title="Renamed")
        assert resp.status_code == 302
        assert resp.url == reverse("quizzmaker:rounds", kwargs={"pk": quiz.pk})
        quiz.refresh_from_db()
        assert quiz.title == "Renamed"

    def test_other_user_gets_404(self, client, quiz, other_user):
        client.login(username="otheruser", password="otherpass123")
        resp = self._post(client, quiz, title="Hacked")
        assert resp.status_code == 404
        quiz.refresh_from_db()
        assert quiz.title != "Hacked"

    def test_get_not_allowed(self, authenticated_client, quiz):
        resp = authenticated_client.get(reverse("quizzmaker:edit", kwargs={"pk": quiz.pk}))
        assert resp.status_code == 405

    def test_invalid_update_flashes_error_and_redirects(self, authenticated_client, quiz):
        # Empty title is invalid (CharField required)
        resp = self._post(authenticated_client, quiz, title="")
        assert resp.status_code == 302
        # Title not persisted
        quiz.refresh_from_db()
        assert quiz.title != ""
        # Error flashed via messages
        messages = list(resp.wsgi_request._messages)  # type: ignore[attr-defined]
        assert any("Title" in str(m) for m in messages)

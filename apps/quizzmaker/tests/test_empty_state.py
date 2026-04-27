"""Tests for quiz list empty-state rendering."""

import pytest
from django.urls import reverse

from apps.quizzmaker.tests.factories import QuizFactory

HOME_URL = reverse("quizzmaker:home")


@pytest.mark.django_db
class TestEmptyState:
    def test_no_results_for_search_shows_message(self, client, other_user):
        QuizFactory(user=other_user, title="Something")
        resp = client.get(HOME_URL + "?q=zzznomatch")
        assert b"No quizzes match" in resp.content or b"no quizzes match" in resp.content.lower()

    def test_empty_public_list_shows_message(self, client):
        resp = client.get(HOME_URL)
        assert b"No quizzes yet" in resp.content or b"no quizzes yet" in resp.content.lower()

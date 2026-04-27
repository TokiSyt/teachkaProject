"""Tests for HomeView (quiz list, search, scope)."""

import pytest
from django.urls import reverse

from apps.quizzmaker.models import Quiz
from apps.quizzmaker.tests.factories import QuizFactory, RoundFactory

HOME_URL = reverse("quizzmaker:home")


@pytest.mark.django_db
class TestHomeViewScope:
    def test_default_scope_lists_only_public(self, client, user, other_user):
        QuizFactory(user=other_user, title="Pub", visibility=Quiz.PUBLIC)
        QuizFactory(user=other_user, title="Priv", visibility=Quiz.PRIVATE)
        resp = client.get(HOME_URL)
        assert resp.status_code == 200
        titles = [q.title for q in resp.context["quizzes"]]
        assert "Pub" in titles
        assert "Priv" not in titles

    def test_mine_scope_lists_only_my_quizzes(self, authenticated_client, user, other_user):
        QuizFactory(user=user, title="Mine", visibility=Quiz.PRIVATE)
        QuizFactory(user=other_user, title="Theirs", visibility=Quiz.PUBLIC)
        resp = authenticated_client.get(HOME_URL + "?scope=mine")
        titles = [q.title for q in resp.context["quizzes"]]
        assert titles == ["Mine"]

    def test_anonymous_mine_scope_redirects_to_login(self, client):
        resp = client.get(HOME_URL + "?scope=mine")
        assert resp.status_code == 302
        assert "/login" in resp.url.lower() or "login" in resp.url


@pytest.mark.django_db
class TestHomeViewSearch:
    def test_query_filters_by_title_icontains(self, client, other_user):
        QuizFactory(user=other_user, title="Capitals of Europe")
        QuizFactory(user=other_user, title="Math basics")
        resp = client.get(HOME_URL + "?q=capitals")
        titles = [q.title for q in resp.context["quizzes"]]
        assert titles == ["Capitals of Europe"]

    def test_empty_query_lists_all_in_scope(self, client, other_user):
        QuizFactory(user=other_user, title="A")
        QuizFactory(user=other_user, title="B")
        resp = client.get(HOME_URL + "?q=")
        assert len(resp.context["quizzes"]) == 2

    def test_no_match_returns_empty_list(self, client, other_user):
        QuizFactory(user=other_user, title="Anything")
        resp = client.get(HOME_URL + "?q=nomatchxyz")
        assert list(resp.context["quizzes"]) == []


@pytest.mark.django_db
class TestHomeViewAnnotations:
    def test_timeless_rounds_count_annotated(self, client, other_user):
        q = QuizFactory(user=other_user)
        RoundFactory(quiz=q, time_limit=0, order=1)
        RoundFactory(quiz=q, time_limit=10, order=2)
        RoundFactory(quiz=q, time_limit=0, order=3)
        resp = client.get(HOME_URL)
        listed = list(resp.context["quizzes"])
        assert listed[0].timeless_rounds == 2


@pytest.mark.django_db
class TestHomeViewPartial:
    def test_partial_renders_quiz_region_template(self, client):
        resp = client.get(HOME_URL + "?partial=1")
        assert resp.status_code == 200
        templates = [t.name for t in resp.templates if t.name]
        assert "quizzmaker/_quiz_region.html" in templates
        assert "quizzmaker/home.html" not in templates

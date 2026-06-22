"""Tests for round CRUD views (create/update/delete/reorder)."""

import json

import pytest
from django.urls import reverse

from apps.quizzmaker.models import Answer, Round
from apps.quizzmaker.tests.factories import AnswerFactory, RoundFactory


@pytest.mark.django_db
class TestRoundCreate:
    def _post(self, client, quiz, **fields):
        defaults = {
            "question": "Q?",
            "question_type": Round.SELECT_CORRECT,
            "time_limit": 30,
            "points": 10,
            "focus_x": 50,
            "focus_y": 50,
        }
        defaults.update(fields)
        return client.post(
            reverse("quizzmaker:round_create", kwargs={"pk": quiz.pk}),
            data=defaults,
        )

    def test_creates_round_attached_to_quiz(self, authenticated_client, quiz):
        resp = self._post(authenticated_client, quiz)
        assert resp.status_code == 302
        assert quiz.rounds.count() == 1

    def test_select_correct_seeds_four_blank_answers(self, authenticated_client, quiz):
        self._post(authenticated_client, quiz, question_type=Round.SELECT_CORRECT)
        r = quiz.rounds.first()
        assert r.answers.count() == 4
        assert all(a.text == "" for a in r.answers.all())

    def test_type_input_seeds_one_answer(self, authenticated_client, quiz):
        self._post(authenticated_client, quiz, question_type=Round.TYPE_INPUT)
        r = quiz.rounds.first()
        assert r.answers.count() == 1

    def test_recalculates_quiz_totals(self, authenticated_client, quiz):
        self._post(authenticated_client, quiz, time_limit=120, points=50)
        quiz.refresh_from_db()
        assert quiz.expected_duration == 2
        assert quiz.total_points == 50

    def test_assigns_sequential_order(self, authenticated_client, quiz):
        self._post(authenticated_client, quiz)
        self._post(authenticated_client, quiz)
        orders = list(quiz.rounds.values_list("order", flat=True))
        assert orders == [1, 2]

    def test_other_user_cannot_create(self, client, quiz, other_user):
        client.login(username="otheruser", password="otherpass123")
        resp = self._post(client, quiz)
        assert resp.status_code == 404


@pytest.mark.django_db
class TestRoundUpdate:
    def _post(self, client, quiz, round_obj, **fields):
        defaults = {
            "question": round_obj.question,
            "question_type": round_obj.question_type,
            "time_limit": round_obj.time_limit,
            "points": round_obj.points,
            "focus_x": round_obj.focus_x,
            "focus_y": round_obj.focus_y,
        }
        defaults.update(fields)
        return client.post(
            reverse("quizzmaker:round_edit", kwargs={"pk": quiz.pk, "round_pk": round_obj.pk}),
            data=defaults,
        )

    def test_saves_time_limit_change(self, authenticated_client, quiz, round_obj):
        self._post(authenticated_client, quiz, round_obj, time_limit=5)
        round_obj.refresh_from_db()
        assert round_obj.time_limit == 5

    def test_recalculates_quiz_totals_on_save(self, authenticated_client, quiz, round_obj):
        self._post(authenticated_client, quiz, round_obj, time_limit=180, points=99)
        quiz.refresh_from_db()
        assert quiz.expected_duration == 3
        assert quiz.total_points == 99

    def test_question_type_change_reseeds_answers(self, authenticated_client, quiz, round_obj):
        # Round starts as SELECT_CORRECT with 0 answers; switch to TYPE_INPUT
        assert round_obj.question_type == Round.SELECT_CORRECT
        self._post(authenticated_client, quiz, round_obj, question_type=Round.TYPE_INPUT)
        round_obj.refresh_from_db()
        assert round_obj.question_type == Round.TYPE_INPUT
        assert round_obj.answers.count() == 1


@pytest.mark.django_db
class TestRoundDelete:
    def test_deletes_round(self, authenticated_client, quiz, round_obj):
        url = reverse("quizzmaker:round_delete", kwargs={"pk": quiz.pk, "round_pk": round_obj.pk})
        authenticated_client.post(url)
        assert quiz.rounds.count() == 0

    def test_recompacts_orders(self, authenticated_client, quiz):
        r1 = RoundFactory(quiz=quiz, order=1)
        r2 = RoundFactory(quiz=quiz, order=2)
        r3 = RoundFactory(quiz=quiz, order=3)
        url = reverse("quizzmaker:round_delete", kwargs={"pk": quiz.pk, "round_pk": r2.pk})
        authenticated_client.post(url)
        r1.refresh_from_db()
        r3.refresh_from_db()
        assert r1.order == 1
        assert r3.order == 2

    def test_recalculates_quiz_totals(self, authenticated_client, quiz):
        RoundFactory(quiz=quiz, time_limit=120, points=20, order=1)
        r2 = RoundFactory(quiz=quiz, time_limit=60, points=30, order=2)
        url = reverse("quizzmaker:round_delete", kwargs={"pk": quiz.pk, "round_pk": r2.pk})
        authenticated_client.post(url)
        quiz.refresh_from_db()
        assert quiz.expected_duration == 2
        assert quiz.total_points == 20


@pytest.mark.django_db
class TestRoundCopyTime:
    def _post(self, client, quiz, round_obj, **data):
        url = reverse("quizzmaker:round_copy_time", kwargs={"pk": quiz.pk, "round_pk": round_obj.pk})
        return client.post(url, data=data)

    def test_copies_value_to_every_round(self, authenticated_client, quiz):
        r1 = RoundFactory(quiz=quiz, time_limit=15, order=1)
        r2 = RoundFactory(quiz=quiz, time_limit=99, order=2)
        r3 = RoundFactory(quiz=quiz, time_limit=42, order=3)
        resp = self._post(authenticated_client, quiz, r1, time_limit=20)
        assert resp.status_code == 302
        for r in (r1, r2, r3):
            r.refresh_from_db()
            assert r.time_limit == 20

    def test_falls_back_to_saved_value_on_bad_input(self, authenticated_client, quiz):
        r1 = RoundFactory(quiz=quiz, time_limit=7, order=1)
        r2 = RoundFactory(quiz=quiz, time_limit=99, order=2)
        self._post(authenticated_client, quiz, r1, time_limit="abc")
        r2.refresh_from_db()
        assert r2.time_limit == 7

    def test_recalculates_quiz_totals(self, authenticated_client, quiz):
        r1 = RoundFactory(quiz=quiz, time_limit=30, order=1)
        RoundFactory(quiz=quiz, time_limit=30, order=2)
        self._post(authenticated_client, quiz, r1, time_limit=60)
        quiz.refresh_from_db()
        assert quiz.expected_duration == 2  # 60 + 60 = 120s -> 2 min

    def test_other_user_cannot_copy(self, client, quiz, round_obj, other_user):
        client.login(username="otheruser", password="otherpass123")
        assert self._post(client, quiz, round_obj, time_limit=10).status_code == 404


@pytest.mark.django_db
class TestRoundReorder:
    def test_reorders_by_id_list(self, authenticated_client, quiz):
        r1 = RoundFactory(quiz=quiz, order=1)
        r2 = RoundFactory(quiz=quiz, order=2)
        r3 = RoundFactory(quiz=quiz, order=3)
        url = reverse("quizzmaker:round_reorder", kwargs={"pk": quiz.pk})
        resp = authenticated_client.post(
            url,
            data=json.dumps({"order": [r3.pk, r1.pk, r2.pk]}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        r1.refresh_from_db()
        r2.refresh_from_db()
        r3.refresh_from_db()
        assert (r3.order, r1.order, r2.order) == (1, 2, 3)

    def test_rejects_id_set_mismatch(self, authenticated_client, quiz):
        r1 = RoundFactory(quiz=quiz, order=1)
        url = reverse("quizzmaker:round_reorder", kwargs={"pk": quiz.pk})
        resp = authenticated_client.post(
            url,
            data=json.dumps({"order": [r1.pk, 99999]}),
            content_type="application/json",
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestQuizFinalize:
    def test_recalculates_totals_and_redirects_home(self, authenticated_client, quiz):
        r = RoundFactory(quiz=quiz, time_limit=90, points=20, order=1)
        AnswerFactory(round=r, text="A", is_correct=True)
        resp = authenticated_client.post(reverse("quizzmaker:quiz_finalize", kwargs={"pk": quiz.pk}))
        assert resp.status_code == 302
        assert resp.url == reverse("quizzmaker:home")
        quiz.refresh_from_db()
        assert quiz.expected_duration == 2
        assert quiz.total_points == 20


@pytest.mark.django_db
class TestAnswerUpdate:
    def test_updates_text(self, authenticated_client, quiz, round_obj):
        ans = AnswerFactory(round=round_obj, text="old")
        url = reverse("quizzmaker:answer_update", kwargs={"pk": quiz.pk, "answer_pk": ans.pk})
        authenticated_client.post(url, {"text": "new"})
        ans.refresh_from_db()
        assert ans.text == "new"

    def test_updates_is_correct(self, authenticated_client, quiz, round_obj):
        ans = AnswerFactory(round=round_obj, is_correct=False)
        url = reverse("quizzmaker:answer_update", kwargs={"pk": quiz.pk, "answer_pk": ans.pk})
        authenticated_client.post(url, {"is_correct": "true"})
        ans.refresh_from_db()
        assert ans.is_correct is True

    def test_other_user_cannot_update(self, client, quiz, round_obj, other_user):
        ans = AnswerFactory(round=round_obj, text="old")
        client.login(username="otheruser", password="otherpass123")
        url = reverse("quizzmaker:answer_update", kwargs={"pk": quiz.pk, "answer_pk": ans.pk})
        resp = client.post(url, {"text": "hacked"})
        assert resp.status_code == 404


@pytest.mark.django_db
class TestAnswerCreateDelete:
    def test_create_adds_blank_answer(self, authenticated_client, quiz, round_obj):
        url = reverse("quizzmaker:answer_create", kwargs={"pk": quiz.pk, "round_pk": round_obj.pk})
        resp = authenticated_client.post(url)
        assert resp.status_code == 200
        assert resp.json()["ok"] is True
        assert round_obj.answers.count() == 1

    def test_delete_removes_answer(self, authenticated_client, quiz, round_obj):
        a1 = AnswerFactory(round=round_obj, text="one")
        AnswerFactory(round=round_obj, text="two")
        url = reverse("quizzmaker:answer_delete", kwargs={"pk": quiz.pk, "answer_pk": a1.pk})
        resp = authenticated_client.post(url)
        assert resp.status_code == 200
        assert round_obj.answers.count() == 1

    def test_cannot_delete_last_answer(self, authenticated_client, quiz, round_obj):
        only = AnswerFactory(round=round_obj, text="solo")
        url = reverse("quizzmaker:answer_delete", kwargs={"pk": quiz.pk, "answer_pk": only.pk})
        resp = authenticated_client.post(url)
        assert resp.status_code == 400
        assert round_obj.answers.count() == 1

    def test_other_user_cannot_create(self, client, quiz, round_obj, other_user):
        client.login(username="otheruser", password="otherpass123")
        url = reverse("quizzmaker:answer_create", kwargs={"pk": quiz.pk, "round_pk": round_obj.pk})
        assert client.post(url).status_code == 404


@pytest.mark.django_db
class TestRoundEditorViewIsReadOnly:
    """Editor GET must not mutate DB (no answer auto-create on render)."""

    def test_get_does_not_create_answers(self, authenticated_client, quiz, round_obj):
        before = Answer.objects.count()
        url = reverse("quizzmaker:rounds", kwargs={"pk": quiz.pk})
        resp = authenticated_client.get(url)
        assert resp.status_code == 200
        assert Answer.objects.count() == before

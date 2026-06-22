"""Round completeness + finalize gating.

A round is "complete" when its correct answer is defined:
- select_correct: at least one answer marked correct AND non-empty.
- type_input: the stored answer text is non-empty.

A quiz cannot be finalized (Save & leave) while any round is incomplete.
"""

import pytest
from django.urls import reverse

from apps.quizzmaker.models import Round
from apps.quizzmaker.tests.factories import AnswerFactory, RoundFactory


@pytest.mark.django_db
class TestRoundHasCorrectAnswer:
    def test_select_correct_incomplete_without_marked_answer(self, quiz):
        r = RoundFactory(quiz=quiz, question_type=Round.SELECT_CORRECT)
        AnswerFactory(round=r, text="A", is_correct=False)
        assert r.has_correct_answer is False

    def test_select_correct_complete_with_marked_answer(self, quiz):
        r = RoundFactory(quiz=quiz, question_type=Round.SELECT_CORRECT)
        AnswerFactory(round=r, text="A", is_correct=True)
        assert r.has_correct_answer is True

    def test_select_correct_complete_when_marked_even_if_text_blank(self, quiz):
        # Marking an option correct is the teacher's choice; an empty label is a
        # separate concern and does not un-set "has a correct answer".
        r = RoundFactory(quiz=quiz, question_type=Round.SELECT_CORRECT)
        AnswerFactory(round=r, text="", is_correct=True)
        assert r.has_correct_answer is True

    def test_type_input_incomplete_when_blank(self, quiz):
        r = RoundFactory(quiz=quiz, question_type=Round.TYPE_INPUT)
        AnswerFactory(round=r, text="", is_correct=False)
        assert r.has_correct_answer is False

    def test_type_input_complete_with_text(self, quiz):
        r = RoundFactory(quiz=quiz, question_type=Round.TYPE_INPUT)
        AnswerFactory(round=r, text="paris", is_correct=False)
        assert r.has_correct_answer is True

    def test_type_input_accept_all_complete_without_text(self, quiz):
        # accept_all rounds are playable with no defined answer.
        r = RoundFactory(quiz=quiz, question_type=Round.TYPE_INPUT, accept_all=True)
        AnswerFactory(round=r, text="", is_correct=False)
        assert r.has_correct_answer is True


@pytest.mark.django_db
class TestFinalizeGating:
    def _finalize(self, client, quiz):
        return client.post(reverse("quizzmaker:quiz_finalize", kwargs={"pk": quiz.pk}))

    def test_blocked_when_a_round_is_incomplete(self, authenticated_client, quiz):
        r = RoundFactory(quiz=quiz, question_type=Round.SELECT_CORRECT)
        AnswerFactory(round=r, text="A", is_correct=False)
        resp = self._finalize(authenticated_client, quiz)
        assert resp.status_code == 302
        assert resp.url == reverse("quizzmaker:rounds", kwargs={"pk": quiz.pk})

    def test_allowed_when_all_rounds_complete(self, authenticated_client, quiz):
        r = RoundFactory(quiz=quiz, question_type=Round.SELECT_CORRECT)
        AnswerFactory(round=r, text="A", is_correct=True)
        resp = self._finalize(authenticated_client, quiz)
        assert resp.status_code == 302
        assert resp.url == reverse("quizzmaker:home")

    def test_allowed_when_quiz_has_no_rounds(self, authenticated_client, quiz):
        resp = self._finalize(authenticated_client, quiz)
        assert resp.status_code == 302
        assert resp.url == reverse("quizzmaker:home")

"""Round snapshot built for live play (live._build_rounds_snapshot).

A select_correct round is single-select when exactly one answer is correct,
multi-select when two or more are. This flag drives the player UI (radio vs
checkbox) without leaking which option is correct.
"""

import pytest

from apps.quizzmaker import live
from apps.quizzmaker.models import Round
from apps.quizzmaker.tests.factories import AnswerFactory, RoundFactory


@pytest.mark.django_db
class TestSingleSelectFlag:
    def test_one_correct_is_single_select(self, quiz):
        r = RoundFactory(quiz=quiz, question_type=Round.SELECT_CORRECT)
        AnswerFactory(round=r, text="A", is_correct=True)
        AnswerFactory(round=r, text="B", is_correct=False)
        snap = live._build_rounds_snapshot(quiz)
        assert snap[0]["single_select"] is True

    def test_two_correct_is_multi_select(self, quiz):
        r = RoundFactory(quiz=quiz, question_type=Round.SELECT_CORRECT)
        AnswerFactory(round=r, text="A", is_correct=True)
        AnswerFactory(round=r, text="B", is_correct=True)
        snap = live._build_rounds_snapshot(quiz)
        assert snap[0]["single_select"] is False


@pytest.mark.django_db
class TestTypeInputAcceptsMany:
    def test_snapshot_collects_all_non_blank_answers(self, quiz):
        r = RoundFactory(quiz=quiz, question_type=Round.TYPE_INPUT)
        AnswerFactory(round=r, text="Paris")
        AnswerFactory(round=r, text="paris, france")
        AnswerFactory(round=r, text="")  # blank ignored
        snap = live._build_rounds_snapshot(quiz)
        assert snap[0]["correct_texts"] == ["paris", "paris, france"]

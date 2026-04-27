"""Tests for quizzmaker models."""

import pytest

from apps.quizzmaker.models import Round
from apps.quizzmaker.tests.factories import QuizFactory, RoundFactory


@pytest.mark.django_db
class TestRecalculateTotals:
    def test_no_rounds_gives_one_minute_and_zero_points(self):
        quiz = QuizFactory()
        quiz.recalculate_totals()
        assert quiz.expected_duration == 1
        assert quiz.total_points == 0

    def test_sums_points(self):
        quiz = QuizFactory()
        RoundFactory(quiz=quiz, points=5, time_limit=0, order=1)
        RoundFactory(quiz=quiz, points=15, time_limit=0, order=2)
        quiz.recalculate_totals()
        assert quiz.total_points == 20

    def test_ceil_to_nearest_minute(self):
        quiz = QuizFactory()
        # 65s should ceil to 2m, not round to 1m
        RoundFactory(quiz=quiz, time_limit=65, points=0, order=1)
        quiz.recalculate_totals()
        assert quiz.expected_duration == 2

    def test_short_time_floors_to_one_minute(self):
        quiz = QuizFactory()
        RoundFactory(quiz=quiz, time_limit=5, points=0, order=1)
        quiz.recalculate_totals()
        assert quiz.expected_duration == 1

    def test_persists_to_db(self):
        quiz = QuizFactory()
        RoundFactory(quiz=quiz, time_limit=120, points=42, order=1)
        quiz.recalculate_totals()
        quiz.refresh_from_db()
        assert quiz.expected_duration == 2
        assert quiz.total_points == 42


@pytest.mark.django_db
class TestQuizDefaults:
    def test_new_quiz_expected_duration_defaults_to_one(self, user):
        from apps.quizzmaker.models import Quiz
        q = Quiz.objects.create(user=user, title="Fresh")
        assert q.expected_duration == 1


@pytest.mark.django_db
class TestRoundOrdering:
    def test_rounds_ordered_by_order_then_id(self, quiz):
        r2 = RoundFactory(quiz=quiz, order=2)
        r1 = RoundFactory(quiz=quiz, order=1)
        assert list(quiz.rounds.all()) == [r1, r2]


@pytest.mark.django_db
class TestRoundQuestionTypes:
    def test_default_is_select_correct(self, quiz):
        r = RoundFactory(quiz=quiz)
        assert r.question_type == Round.SELECT_CORRECT


@pytest.mark.django_db
class TestRoundStringRepresentation:
    def test_str_uses_order_not_stored_title(self, quiz):
        r = RoundFactory(quiz=quiz, order=3)
        assert "Round 3" in str(r)

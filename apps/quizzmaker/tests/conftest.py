"""Pytest fixtures for quizzmaker app tests."""

import pytest

from apps.quizzmaker.models import Quiz, Round


@pytest.fixture
def quiz(db, user):
    return Quiz.objects.create(user=user, title="My Quiz", visibility=Quiz.PUBLIC)


@pytest.fixture
def private_quiz(db, user):
    return Quiz.objects.create(user=user, title="Private Quiz", visibility=Quiz.PRIVATE)


@pytest.fixture
def round_obj(db, quiz):
    return Round.objects.create(
        quiz=quiz,
        question="Q1",
        order=1,
        question_type=Round.SELECT_CORRECT,
        points=10,
        time_limit=30,
    )

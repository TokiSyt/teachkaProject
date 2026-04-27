"""Factory Boy factories for quizzmaker app."""

import factory
from django.contrib.auth import get_user_model

from apps.quizzmaker.models import Answer, Quiz, Round


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"qmuser{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")


class QuizFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Quiz

    user = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Quiz {n}")
    visibility = Quiz.PUBLIC


class RoundFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Round

    quiz = factory.SubFactory(QuizFactory)
    question = "What?"
    order = factory.Sequence(lambda n: n + 1)
    question_type = Round.SELECT_CORRECT
    points = 10
    time_limit = 30


class AnswerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Answer

    round = factory.SubFactory(RoundFactory)
    text = "Answer"
    is_correct = False
    order = factory.Sequence(lambda n: n + 1)

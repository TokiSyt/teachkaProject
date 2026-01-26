"""Factory Boy factories for group_maker app."""

import factory
from django.contrib.auth import get_user_model

from apps.group_maker.models import GroupCreationModel


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating test users."""

    class Meta:
        model = get_user_model()
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")


class GroupCreationModelFactory(factory.django.DjangoModelFactory):
    """Factory for creating test groups."""

    class Meta:
        model = GroupCreationModel

    user = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Group {n}")
    members_string = "Alice, Bob, Charlie"

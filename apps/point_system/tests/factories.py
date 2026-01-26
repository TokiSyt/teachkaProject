"""Factory Boy factories for point_system app."""

import factory

from apps.group_maker.tests.factories import GroupCreationModelFactory
from apps.point_system.models import FieldDefinition, Member


class MemberFactory(factory.django.DjangoModelFactory):
    """Factory for creating test members."""

    class Meta:
        model = Member

    group = factory.SubFactory(GroupCreationModelFactory)
    name = factory.Sequence(lambda n: f"Member {n}")
    positive_data = factory.LazyFunction(dict)
    negative_data = factory.LazyFunction(dict)


class FieldDefinitionFactory(factory.django.DjangoModelFactory):
    """Factory for creating test field definitions."""

    class Meta:
        model = FieldDefinition

    group = factory.SubFactory(GroupCreationModelFactory)
    name = factory.Sequence(lambda n: f"field_{n}")
    type = "int"
    definition = "positive"

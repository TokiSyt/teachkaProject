"""Pytest fixtures for point_system app tests."""

import pytest

from apps.group_maker.models import GroupCreationModel
from apps.point_system.models import FieldDefinition


@pytest.fixture
def group_with_fields(db, user):
    """Create a group with field definitions."""
    group = GroupCreationModel.objects.create(
        user=user,
        title="Test Group",
        members_string="Alice, Bob",
    )

    # Create positive field
    FieldDefinition.objects.create(
        group=group,
        name="homework",
        type="int",
        definition="positive",
    )

    # Create negative field
    FieldDefinition.objects.create(
        group=group,
        name="tardiness",
        type="int",
        definition="negative",
    )

    # Delete existing members and re-sync to pick up field definitions
    group.karma_members.all().delete()
    group.sync_members()

    return group


@pytest.fixture
def member_with_data(db, group_with_fields):
    """Get a member with test data."""
    member = group_with_fields.karma_members.first()
    member.positive_data = {"homework": 10}
    member.negative_data = {"tardiness": 3}
    member.save()
    return member

"""Pytest fixtures for group_maker app tests."""

import pytest

from apps.group_maker.models import GroupCreationModel


@pytest.fixture
def group(db, user):
    """Create a test group."""
    return GroupCreationModel.objects.create(
        user=user,
        title="Test Group",
        members_string="Alice, Bob, Charlie",
    )


@pytest.fixture
def empty_group(db, user):
    """Create a group with minimal data."""
    return GroupCreationModel.objects.create(
        user=user,
        title="Empty Group",
        members_string="SingleMember",
    )

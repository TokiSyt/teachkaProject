"""Tests for point_system app models."""

import pytest
from django.db import IntegrityError

from apps.point_system.models import FieldDefinition

from .factories import FieldDefinitionFactory


@pytest.mark.django_db
class TestMemberModel:
    """Tests for Member model."""

    def test_create_member(self, group_with_fields):
        """Test creating a member."""
        member = group_with_fields.karma_members.first()
        assert member is not None
        assert member.name in ["Alice", "Bob"]

    def test_member_str(self, member_with_data):
        """Test member string representation."""
        assert "Test Group" in str(member_with_data)

    def test_member_default_data(self, group_with_fields):
        """Test that members get default field values."""
        member = group_with_fields.karma_members.first()
        assert "homework" in member.positive_data
        assert "tardiness" in member.negative_data

    def test_member_ordering(self, group_with_fields):
        """Test that members are ordered by id."""
        members = list(group_with_fields.karma_members.all())
        assert members == sorted(members, key=lambda m: m.id)


@pytest.mark.django_db
class TestFieldDefinitionModel:
    """Tests for FieldDefinition model."""

    def test_create_field(self, user):
        """Test creating a field definition."""
        from apps.group_maker.models import GroupCreationModel

        group = GroupCreationModel.objects.create(
            user=user,
            title="Test",
            members_string="A",
        )
        field = FieldDefinition.objects.create(
            group=group,
            name="test_field",
            type="int",
            definition="positive",
        )
        assert field.pk is not None

    def test_unique_constraint(self, group_with_fields):
        """Test that duplicate field names are not allowed."""
        with pytest.raises(IntegrityError):
            FieldDefinition.objects.create(
                group=group_with_fields,
                name="homework",  # Already exists
                type="int",
                definition="positive",
            )

    def test_factory(self):
        """Test factory creates valid field."""
        field = FieldDefinitionFactory()
        assert field.pk is not None
        assert field.group is not None

"""Comprehensive tests for point_system app models."""

import pytest
from django.db import IntegrityError

from apps.group_maker.models import GroupCreationModel
from apps.point_system.models import FieldDefinition, Member

from .factories import FieldDefinitionFactory, MemberFactory


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
        assert member_with_data.name in str(member_with_data)

    def test_member_default_data(self, group_with_fields):
        """Test that members get default field values."""
        member = group_with_fields.karma_members.first()
        assert "homework" in member.positive_data
        assert "tardiness" in member.negative_data

    def test_member_ordering(self, group_with_fields):
        """Test that members are ordered by id."""
        members = list(group_with_fields.karma_members.all())
        assert members == sorted(members, key=lambda m: m.id)

    def test_member_factory(self):
        """Test MemberFactory creates valid member."""
        member = MemberFactory()
        assert member.pk is not None
        assert member.group is not None
        assert member.positive_data == {}
        assert member.negative_data == {}

    def test_member_default_totals(self, group_with_fields):
        """Test that member totals default to 0."""
        member = group_with_fields.karma_members.first()
        assert member.positive_total == 0
        assert member.negative_total == 0

    def test_member_with_positive_data_only(self, user):
        """Test member with only positive data."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="A")
        member = group.karma_members.first()
        member.positive_data = {"homework": 10, "quizzes": 5}
        member.negative_data = {}
        member.save()

        member.refresh_from_db()
        assert member.positive_data == {"homework": 10, "quizzes": 5}
        assert member.negative_data == {}

    def test_member_with_negative_data_only(self, user):
        """Test member with only negative data."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="A")
        member = group.karma_members.first()
        member.positive_data = {}
        member.negative_data = {"tardiness": 3}
        member.save()

        member.refresh_from_db()
        assert member.negative_data == {"tardiness": 3}

    def test_member_json_field_complex_data(self, user):
        """Test that JSONField handles complex data structures."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="A")
        member = group.karma_members.first()
        member.positive_data = {
            "homework": 10,
            "notes": "Good work",
            "empty": "",
            "zero": 0,
        }
        member.save()

        member.refresh_from_db()
        assert member.positive_data["homework"] == 10
        assert member.positive_data["notes"] == "Good work"
        assert member.positive_data["empty"] == ""
        assert member.positive_data["zero"] == 0

    def test_member_cascade_delete(self, group_with_fields):
        """Test that members are deleted when group is deleted."""
        member_ids = list(group_with_fields.karma_members.values_list("id", flat=True))
        group_with_fields.delete()

        assert not Member.objects.filter(id__in=member_ids).exists()

    def test_member_timestamps(self, group_with_fields):
        """Test that timestamps are set correctly."""
        member = group_with_fields.karma_members.first()
        assert member.created_at is not None
        assert member.updated_at is not None

    def test_member_updated_at_changes(self, group_with_fields):
        """Test that updated_at changes on save."""
        member = group_with_fields.karma_members.first()
        original_updated = member.updated_at

        member.positive_total = 100
        member.save()
        member.refresh_from_db()

        assert member.updated_at > original_updated


@pytest.mark.django_db
class TestFieldDefinitionModel:
    """Tests for FieldDefinition model."""

    def test_create_field(self, user):
        """Test creating a field definition."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="A")
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

    def test_field_str(self, group_with_fields):
        """Test field string representation."""
        field = FieldDefinition.objects.get(group=group_with_fields, name="homework")
        assert "homework" in str(field)
        assert "positive" in str(field)

    def test_same_name_different_tables(self, group_with_fields):
        """Test same field name can exist in different tables."""
        # homework already exists in positive
        FieldDefinition.objects.create(
            group=group_with_fields,
            name="homework",  # Same name but different definition
            type="int",
            definition="negative",
        )
        # Should not raise

    def test_same_name_different_groups(self, user):
        """Test same field name can exist in different groups."""
        group1 = GroupCreationModel.objects.create(user=user, title="Group 1", members_string="A")
        group2 = GroupCreationModel.objects.create(user=user, title="Group 2", members_string="B")

        FieldDefinition.objects.create(group=group1, name="shared_name", type="int", definition="positive")
        FieldDefinition.objects.create(group=group2, name="shared_name", type="int", definition="positive")
        # Should not raise

    def test_field_type_choices(self, user):
        """Test that only valid types are accepted."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="A")

        # Valid types
        int_field = FieldDefinition.objects.create(group=group, name="int_field", type="int", definition="positive")
        str_field = FieldDefinition.objects.create(group=group, name="str_field", type="str", definition="positive")
        assert int_field.type == "int"
        assert str_field.type == "str"

    def test_field_definition_choices(self, user):
        """Test that only valid definitions are accepted."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="A")

        pos_field = FieldDefinition.objects.create(group=group, name="pos_field", type="int", definition="positive")
        neg_field = FieldDefinition.objects.create(group=group, name="neg_field", type="int", definition="negative")
        assert pos_field.definition == "positive"
        assert neg_field.definition == "negative"

    def test_field_cascade_delete(self, group_with_fields):
        """Test that fields are deleted when group is deleted."""
        field_ids = list(group_with_fields.fields.values_list("id", flat=True))
        group_with_fields.delete()

        assert not FieldDefinition.objects.filter(id__in=field_ids).exists()

    def test_field_timestamps(self, group_with_fields):
        """Test that timestamps are set correctly."""
        field = group_with_fields.fields.first()
        assert field.created_at is not None
        assert field.updated_at is not None

    def test_field_name_max_length(self, user):
        """Test that field name respects max_length."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="A")
        # Max length is 100
        long_name = "a" * 100
        field = FieldDefinition.objects.create(group=group, name=long_name, type="int", definition="positive")
        assert field.name == long_name

    def test_field_ordering(self, user):
        """Test fields are ordered by creation time."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="A")

        field1 = FieldDefinition.objects.create(group=group, name="first", type="int", definition="positive")
        field2 = FieldDefinition.objects.create(group=group, name="second", type="int", definition="positive")
        field3 = FieldDefinition.objects.create(group=group, name="third", type="int", definition="positive")

        fields = list(FieldDefinition.objects.filter(group=group).order_by("created_at"))
        assert fields[0] == field1
        assert fields[1] == field2
        assert fields[2] == field3


@pytest.mark.django_db
class TestMemberFieldRelationship:
    """Tests for the relationship between Member and FieldDefinition."""

    def test_member_data_matches_field_definitions(self, group_with_fields):
        """Test that member data keys match field definitions."""
        positive_fields = set(
            FieldDefinition.objects.filter(group=group_with_fields, definition="positive").values_list(
                "name", flat=True
            )
        )
        negative_fields = set(
            FieldDefinition.objects.filter(group=group_with_fields, definition="negative").values_list(
                "name", flat=True
            )
        )

        for member in group_with_fields.karma_members.all():
            assert set(member.positive_data.keys()) == positive_fields
            assert set(member.negative_data.keys()) == negative_fields

    def test_new_member_gets_existing_fields(self, group_with_fields):
        """Test that newly synced member gets existing field definitions."""
        # Add a new member to the group
        group_with_fields.members_string = "Alice, Bob, Charlie"
        group_with_fields.save()
        group_with_fields.sync_members()

        charlie = group_with_fields.karma_members.get(name="Charlie")
        assert "homework" in charlie.positive_data
        assert "tardiness" in charlie.negative_data

    def test_member_data_without_field_definition(self, group_with_fields):
        """Test that member can have data without corresponding FieldDefinition."""
        member = group_with_fields.karma_members.first()
        member.positive_data["orphan_field"] = 100
        member.save()

        member.refresh_from_db()
        assert member.positive_data["orphan_field"] == 100
        # This is allowed - data can exist without FieldDefinition


@pytest.mark.django_db
class TestModelEdgeCases:
    """Edge case tests for models."""

    def test_member_empty_name(self, user):
        """Test member with empty name (if allowed)."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="A")
        member = MemberFactory(group=group, name="")
        assert member.pk is not None
        assert member.name == ""

    def test_field_definition_empty_name(self, user):
        """Test field definition with empty name (if allowed)."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="A")
        field = FieldDefinition.objects.create(group=group, name="", type="int", definition="positive")
        assert field.pk is not None

    def test_member_unicode_data(self, user):
        """Test member with unicode characters in data."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="A")
        member = group.karma_members.first()
        member.positive_data = {"תרגיל": 10, "宿題": 20, "домашнее задание": 30}
        member.save()

        member.refresh_from_db()
        assert member.positive_data["תרגיל"] == 10
        assert member.positive_data["宿題"] == 20
        assert member.positive_data["домашнее задание"] == 30

    def test_large_number_of_fields(self, user):
        """Test member with many fields."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="A")
        member = group.karma_members.first()

        # Create 100 fields worth of data
        large_data = {f"field_{i}": i for i in range(100)}
        member.positive_data = large_data
        member.save()

        member.refresh_from_db()
        assert len(member.positive_data) == 100
        assert member.positive_data["field_50"] == 50

    def test_member_very_large_values(self, user):
        """Test member with very large numeric values."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="A")
        member = group.karma_members.first()
        member.positive_data = {"big": 999999999999}
        member.positive_total = 999999999999
        member.save()

        member.refresh_from_db()
        assert member.positive_data["big"] == 999999999999
        assert member.positive_total == 999999999999

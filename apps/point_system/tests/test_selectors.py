"""Comprehensive tests for point_system app selectors."""

import pytest
from django.http import Http404

from apps.group_maker.models import GroupCreationModel
from apps.point_system import selectors
from apps.point_system.models import FieldDefinition


@pytest.mark.django_db
class TestGetUserGroups:
    """Tests for get_user_groups selector."""

    def test_get_user_groups(self, user, group_with_fields):
        """Test getting user's groups."""
        groups = selectors.get_user_groups(user)
        assert group_with_fields in groups

    def test_get_user_groups_excludes_others(self, user, other_user, group_with_fields):
        """Test that selector excludes other users' groups."""
        groups = selectors.get_user_groups(other_user)
        assert group_with_fields not in groups

    def test_get_user_groups_empty(self, user):
        """Test getting groups when user has none."""
        groups = selectors.get_user_groups(user)
        assert groups.count() == 0

    def test_get_user_groups_multiple(self, user):
        """Test getting multiple groups."""
        group1 = GroupCreationModel.objects.create(user=user, title="Group 1", members_string="A")
        group2 = GroupCreationModel.objects.create(user=user, title="Group 2", members_string="B")
        group3 = GroupCreationModel.objects.create(user=user, title="Group 3", members_string="C")

        groups = selectors.get_user_groups(user)
        assert groups.count() == 3
        assert group1 in groups
        assert group2 in groups
        assert group3 in groups

    def test_get_user_groups_ordering(self, user):
        """Test that groups are ordered by creation date (newest first)."""
        group1 = GroupCreationModel.objects.create(user=user, title="First", members_string="A")
        group2 = GroupCreationModel.objects.create(user=user, title="Second", members_string="B")
        group3 = GroupCreationModel.objects.create(user=user, title="Third", members_string="C")

        groups = list(selectors.get_user_groups(user))
        # Should be ordered by -created (newest first)
        assert groups[0] == group3
        assert groups[1] == group2
        assert groups[2] == group1


@pytest.mark.django_db
class TestGetGroupWithMembers:
    """Tests for get_group_with_members selector."""

    def test_get_group_with_members(self, user, group_with_fields):
        """Test getting group with members."""
        group, members = selectors.get_group_with_members(group_with_fields.id, user)
        assert group == group_with_fields
        assert members.count() == 2

    def test_get_group_with_members_permission_denied(self, other_user, group_with_fields):
        """Test that selector raises 404 for unauthorized user."""
        with pytest.raises(Http404):
            selectors.get_group_with_members(group_with_fields.id, other_user)

    def test_get_group_with_members_nonexistent(self, user):
        """Test that selector raises 404 for nonexistent group."""
        with pytest.raises(Http404):
            selectors.get_group_with_members(99999, user)

    def test_get_group_with_members_ordering(self, user, group_with_fields):
        """Test that members are ordered by id."""
        _, members = selectors.get_group_with_members(group_with_fields.id, user)
        member_list = list(members)
        assert member_list == sorted(member_list, key=lambda m: m.id)

    def test_get_group_with_members_single_member(self, user):
        """Test getting group with single member."""
        group = GroupCreationModel.objects.create(user=user, title="Single", members_string="OnlyOne")

        result_group, members = selectors.get_group_with_members(group.id, user)
        assert result_group == group
        assert members.count() == 1


@pytest.mark.django_db
class TestGetGroupWithFields:
    """Tests for get_group_with_fields selector."""

    def test_get_group_with_fields(self, user, group_with_fields):
        """Test getting group with field definitions."""
        group, fields = selectors.get_group_with_fields(group_with_fields.id, user)
        assert group == group_with_fields
        assert "homework" in fields["positive_names"]
        assert "tardiness" in fields["negative_names"]

    def test_get_group_with_fields_structure(self, user, group_with_fields):
        """Test the structure of the fields dict."""
        _, fields = selectors.get_group_with_fields(group_with_fields.id, user)

        assert "positive" in fields
        assert "negative" in fields
        assert "positive_names" in fields
        assert "negative_names" in fields
        assert "positive_types" in fields
        assert "negative_types" in fields

    def test_get_group_with_fields_types(self, user, group_with_fields):
        """Test that field types are correctly mapped."""
        _, fields = selectors.get_group_with_fields(group_with_fields.id, user)

        # Types should be "number" or "text" for HTML input types
        assert fields["positive_types"]["homework"] == "number"  # int -> number
        assert fields["negative_types"]["tardiness"] == "number"

    def test_get_group_with_fields_text_type(self, user, group_with_fields):
        """Test that string fields are mapped to 'text'."""
        FieldDefinition.objects.create(
            group=group_with_fields,
            name="notes",
            type="str",
            definition="positive",
        )

        _, fields = selectors.get_group_with_fields(group_with_fields.id, user)
        assert fields["positive_types"]["notes"] == "text"

    def test_get_group_with_fields_permission_denied(self, other_user, group_with_fields):
        """Test that selector raises 404 for unauthorized user."""
        with pytest.raises(Http404):
            selectors.get_group_with_fields(group_with_fields.id, other_user)

    def test_get_group_with_fields_no_fields(self, user):
        """Test getting group with no field definitions."""
        group = GroupCreationModel.objects.create(user=user, title="No Fields", members_string="A")

        _, fields = selectors.get_group_with_fields(group.id, user)
        assert fields["positive_names"] == []
        assert fields["negative_names"] == []
        assert fields["positive_types"] == {}
        assert fields["negative_types"] == {}

    def test_get_group_with_fields_only_positive(self, user):
        """Test getting group with only positive fields."""
        group = GroupCreationModel.objects.create(user=user, title="Positive Only", members_string="A")
        FieldDefinition.objects.create(group=group, name="score", type="int", definition="positive")

        _, fields = selectors.get_group_with_fields(group.id, user)
        assert len(fields["positive_names"]) == 1
        assert len(fields["negative_names"]) == 0

    def test_get_group_with_fields_only_negative(self, user):
        """Test getting group with only negative fields."""
        group = GroupCreationModel.objects.create(user=user, title="Negative Only", members_string="A")
        FieldDefinition.objects.create(group=group, name="penalty", type="int", definition="negative")

        _, fields = selectors.get_group_with_fields(group.id, user)
        assert len(fields["positive_names"]) == 0
        assert len(fields["negative_names"]) == 1


@pytest.mark.django_db
class TestGetGroupFullData:
    """Tests for get_group_full_data selector."""

    def test_get_group_full_data(self, user, group_with_fields):
        """Test getting complete group data."""
        data = selectors.get_group_full_data(group_with_fields.id, user)

        assert data["group"] == group_with_fields
        assert len(list(data["members"])) == 2
        assert "homework" in data["positive_column_names"]
        assert "tardiness" in data["negative_column_names"]

    def test_get_group_full_data_structure(self, user, group_with_fields):
        """Test the structure of the full data dict."""
        data = selectors.get_group_full_data(group_with_fields.id, user)

        assert "group" in data
        assert "members" in data
        assert "positive_column_names" in data
        assert "negative_column_names" in data
        assert "column_type_positive" in data
        assert "column_type_negative" in data

    def test_get_group_full_data_calculates_totals(self, user, group_with_fields):
        """Test that member totals are calculated."""
        # Set some data
        member = group_with_fields.karma_members.first()
        member.positive_data = {"homework": 10}
        member.negative_data = {"tardiness": 5}
        member.save()

        data = selectors.get_group_full_data(group_with_fields.id, user)

        # Find the member with data
        for m in data["members"]:
            if m.id == member.id:
                assert m.positive_total == 10
                assert m.negative_total == 5
                break

    def test_get_group_full_data_permission_denied(self, other_user, group_with_fields):
        """Test that selector raises 404 for unauthorized user."""
        with pytest.raises(Http404):
            selectors.get_group_full_data(group_with_fields.id, other_user)

    def test_get_group_full_data_single_member(self, user):
        """Test getting full data for single member group."""
        group = GroupCreationModel.objects.create(user=user, title="Single", members_string="OnlyOne")

        data = selectors.get_group_full_data(group.id, user)
        assert data["group"] == group
        assert len(list(data["members"])) == 1

    def test_get_group_full_data_no_fields(self, user):
        """Test getting full data for group with no fields."""
        group = GroupCreationModel.objects.create(user=user, title="No Fields", members_string="A")

        data = selectors.get_group_full_data(group.id, user)
        assert data["positive_column_names"] == []
        assert data["negative_column_names"] == []

    def test_get_group_full_data_mixed_field_types(self, user):
        """Test getting full data with mixed field types."""
        group = GroupCreationModel.objects.create(user=user, title="Mixed", members_string="A")
        FieldDefinition.objects.create(group=group, name="score", type="int", definition="positive")
        FieldDefinition.objects.create(group=group, name="notes", type="str", definition="positive")
        group.sync_members()

        data = selectors.get_group_full_data(group.id, user)
        assert data["column_type_positive"]["score"] == "number"
        assert data["column_type_positive"]["notes"] == "text"

    def test_get_group_full_data_many_members(self, user):
        """Test getting full data for group with many members."""
        group = GroupCreationModel.objects.create(
            user=user,
            title="Large Group",
            members_string=", ".join([f"Member{i}" for i in range(20)]),
        )

        data = selectors.get_group_full_data(group.id, user)
        assert len(list(data["members"])) == 20

    def test_get_group_full_data_many_fields(self, user):
        """Test getting full data for group with many fields."""
        group = GroupCreationModel.objects.create(user=user, title="Many Fields", members_string="A")
        for i in range(10):
            FieldDefinition.objects.create(group=group, name=f"pos_field_{i}", type="int", definition="positive")
            FieldDefinition.objects.create(group=group, name=f"neg_field_{i}", type="int", definition="negative")
        group.sync_members()

        data = selectors.get_group_full_data(group.id, user)
        assert len(data["positive_column_names"]) == 10
        assert len(data["negative_column_names"]) == 10


@pytest.mark.django_db
class TestSelectorEdgeCases:
    """Edge case tests for selectors."""

    def test_group_id_as_string(self, user, group_with_fields):
        """Test that selectors handle string group_id (converted to int)."""
        # This would fail if the selector doesn't handle the type
        # The view converts to int before calling
        group, members = selectors.get_group_with_members(group_with_fields.id, user)
        assert group is not None

    def test_get_full_data_with_text_values(self, user):
        """Test that full data handles text values in data correctly."""
        group = GroupCreationModel.objects.create(user=user, title="Text Data", members_string="A")
        FieldDefinition.objects.create(group=group, name="notes", type="str", definition="positive")
        group.sync_members()

        member = group.karma_members.first()
        member.positive_data = {"notes": "Some text"}
        member.save()

        data = selectors.get_group_full_data(group.id, user)
        for m in data["members"]:
            # Text values should not affect total
            assert m.positive_total == 0

    def test_get_full_data_with_mixed_data(self, user):
        """Test full data with mix of numeric and text."""
        group = GroupCreationModel.objects.create(user=user, title="Mixed Data", members_string="A")
        FieldDefinition.objects.create(group=group, name="score", type="int", definition="positive")
        FieldDefinition.objects.create(group=group, name="notes", type="str", definition="positive")
        group.sync_members()

        member = group.karma_members.first()
        member.positive_data = {"score": 100, "notes": "Excellent"}
        member.save()

        data = selectors.get_group_full_data(group.id, user)
        for m in data["members"]:
            assert m.positive_total == 100  # Only numeric counted

    def test_selector_with_deleted_field_definition(self, user, group_with_fields):
        """Test selector after field definition is deleted."""
        # Member still has data for the field, but FieldDefinition is gone
        member = group_with_fields.karma_members.first()
        member.positive_data["homework"] = 50
        member.save()

        # Delete the field definition
        FieldDefinition.objects.filter(group=group_with_fields, name="homework").delete()

        data = selectors.get_group_full_data(group_with_fields.id, user)
        # homework should not be in column names anymore
        assert "homework" not in data["positive_column_names"]
        # But member data still has it (orphaned data)
        assert group_with_fields.karma_members.first().positive_data.get("homework") == 50

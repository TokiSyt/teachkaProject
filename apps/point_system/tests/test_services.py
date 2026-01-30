"""Comprehensive tests for point_system app services."""

import pytest

from apps.group_maker.models import GroupCreationModel
from apps.point_system.models import FieldDefinition
from apps.point_system.services import CalculationService, MemberService


@pytest.mark.django_db
class TestMemberService:
    """Tests for MemberService."""

    def test_update_member_data(self, group_with_fields):
        """Test updating member data."""
        member = group_with_fields.karma_members.first()

        MemberService.update_member_data(
            member,
            positive_data={"homework": 15, "participation": 5},
            negative_data={"tardiness": 2},
        )

        member.refresh_from_db()
        assert member.positive_data == {"homework": 15, "participation": 5}
        assert member.negative_data == {"tardiness": 2}
        assert member.positive_total == 20
        assert member.negative_total == 2

    def test_update_member_positive_only(self, group_with_fields):
        """Test updating only positive data."""
        member = group_with_fields.karma_members.first()
        member.negative_data = {"tardiness": 10}
        member.save()

        MemberService.update_member_data(
            member,
            positive_data={"homework": 25},
        )

        member.refresh_from_db()
        assert member.positive_data == {"homework": 25}
        assert member.negative_data == {"tardiness": 10}  # Unchanged
        assert member.positive_total == 25

    def test_update_member_negative_only(self, group_with_fields):
        """Test updating only negative data."""
        member = group_with_fields.karma_members.first()
        member.positive_data = {"homework": 10}
        member.save()

        MemberService.update_member_data(
            member,
            negative_data={"tardiness": 5},
        )

        member.refresh_from_db()
        assert member.positive_data == {"homework": 10}  # Unchanged
        assert member.negative_data == {"tardiness": 5}
        assert member.negative_total == 5

    def test_update_member_empty_data(self, group_with_fields):
        """Test updating with empty data dictionaries."""
        member = group_with_fields.karma_members.first()
        member.positive_data = {"old": 100}
        member.save()

        MemberService.update_member_data(
            member,
            positive_data={},
            negative_data={},
        )

        member.refresh_from_db()
        assert member.positive_data == {}
        assert member.negative_data == {}
        assert member.positive_total == 0
        assert member.negative_total == 0

    def test_update_member_returns_member(self, group_with_fields):
        """Test that update returns the member instance."""
        member = group_with_fields.karma_members.first()
        result = MemberService.update_member_data(member, positive_data={"test": 1})
        assert result == member

    def test_add_field_to_members(self, group_with_fields):
        """Test adding a new field to all members."""
        MemberService.add_field_to_members(
            group_with_fields,
            field_name="extra_credit",
            field_type="int",
            definition="positive",
        )

        for member in group_with_fields.karma_members.all():
            assert "extra_credit" in member.positive_data
            assert member.positive_data["extra_credit"] == 0

    def test_add_field_str_type(self, group_with_fields):
        """Test adding a string field."""
        MemberService.add_field_to_members(
            group_with_fields,
            field_name="notes",
            field_type="str",
            definition="positive",
        )

        for member in group_with_fields.karma_members.all():
            assert member.positive_data["notes"] == ""

    def test_add_field_to_negative(self, group_with_fields):
        """Test adding a field to negative data."""
        MemberService.add_field_to_members(
            group_with_fields,
            field_name="absences",
            field_type="int",
            definition="negative",
        )

        for member in group_with_fields.karma_members.all():
            assert "absences" in member.negative_data
            assert member.negative_data["absences"] == 0

    def test_add_field_initializes_empty_data(self, user):
        """Test adding field when member data is empty."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="A")
        member = group.karma_members.first()
        member.positive_data = {}
        member.save()

        MemberService.add_field_to_members(
            group,
            field_name="test_field",
            field_type="int",
            definition="positive",
        )

        member.refresh_from_db()
        assert member.positive_data == {"test_field": 0}

    def test_remove_field_from_members(self, group_with_fields):
        """Test removing a field from all members."""
        # First add data to the field
        for member in group_with_fields.karma_members.all():
            member.positive_data["homework"] = 10
            member.save()

        MemberService.remove_field_from_members(
            group_with_fields,
            field_name="homework",
            definition="positive",
        )

        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert "homework" not in member.positive_data

        # Also verify FieldDefinition was deleted
        assert not FieldDefinition.objects.filter(
            group=group_with_fields, name="homework", definition="positive"
        ).exists()

    def test_remove_field_from_negative(self, group_with_fields):
        """Test removing a field from negative data."""
        MemberService.remove_field_from_members(
            group_with_fields,
            field_name="tardiness",
            definition="negative",
        )

        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert "tardiness" not in member.negative_data

    def test_remove_nonexistent_field(self, group_with_fields):
        """Test removing a field that doesn't exist."""
        # Should not raise an error
        MemberService.remove_field_from_members(
            group_with_fields,
            field_name="nonexistent",
            definition="positive",
        )

    def test_remove_field_preserves_other_fields(self, group_with_fields):
        """Test that removing a field preserves other fields."""
        # Add another field
        for member in group_with_fields.karma_members.all():
            member.positive_data["other_field"] = 999
            member.save()

        MemberService.remove_field_from_members(
            group_with_fields,
            field_name="homework",
            definition="positive",
        )

        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert member.positive_data.get("other_field") == 999

    def test_rename_field_for_members(self, group_with_fields):
        """Test renaming a field for all members."""
        # First set some data
        for member in group_with_fields.karma_members.all():
            member.positive_data["homework"] = 10
            member.save()

        MemberService.rename_field_for_members(
            group_with_fields,
            old_name="homework",
            new_name="assignments",
            definition="positive",
        )

        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert "homework" not in member.positive_data
            assert member.positive_data.get("assignments") == 10

        # Verify FieldDefinition was renamed
        assert FieldDefinition.objects.filter(
            group=group_with_fields, name="assignments", definition="positive"
        ).exists()

    def test_rename_field_preserves_data(self, group_with_fields):
        """Test that renaming preserves all data values."""
        members = list(group_with_fields.karma_members.all())
        members[0].positive_data["homework"] = 100
        members[0].save()
        members[1].positive_data["homework"] = 200
        members[1].save()

        MemberService.rename_field_for_members(
            group_with_fields,
            old_name="homework",
            new_name="assignments",
            definition="positive",
        )

        members[0].refresh_from_db()
        members[1].refresh_from_db()
        assert members[0].positive_data["assignments"] == 100
        assert members[1].positive_data["assignments"] == 200

    def test_rename_field_in_negative(self, group_with_fields):
        """Test renaming a field in negative data."""
        for member in group_with_fields.karma_members.all():
            member.negative_data["tardiness"] = 5
            member.save()

        MemberService.rename_field_for_members(
            group_with_fields,
            old_name="tardiness",
            new_name="late_arrivals",
            definition="negative",
        )

        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert member.negative_data.get("late_arrivals") == 5


@pytest.mark.django_db
class TestMemberServiceCalculateTotal:
    """Tests for MemberService._calculate_total."""

    def test_calculate_total_empty(self):
        """Test total calculation with empty data."""
        assert MemberService._calculate_total({}) == 0

    def test_calculate_total_none(self):
        """Test total calculation with None."""
        assert MemberService._calculate_total(None) == 0

    def test_calculate_total_integers(self):
        """Test total calculation with integer values."""
        data = {"a": 10, "b": 20, "c": 30}
        assert MemberService._calculate_total(data) == 60

    def test_calculate_total_with_strings(self):
        """Test total calculation ignores non-numeric strings."""
        data = {"num": 10, "text": "hello", "another_num": 5}
        assert MemberService._calculate_total(data) == 15

    def test_calculate_total_with_numeric_strings(self):
        """Test total calculation converts numeric strings."""
        data = {"a": "10", "b": "20"}
        assert MemberService._calculate_total(data) == 30

    def test_calculate_total_with_zero(self):
        """Test total calculation with zero values."""
        data = {"a": 0, "b": 0, "c": 10}
        assert MemberService._calculate_total(data) == 10

    def test_calculate_total_with_negative_numbers(self):
        """Test total calculation with negative numbers."""
        data = {"a": 10, "b": -5, "c": 3}
        assert MemberService._calculate_total(data) == 8

    def test_calculate_total_mixed_types(self):
        """Test total calculation with mixed types."""
        data = {
            "int": 10,
            "str_num": "20",
            "text": "hello",
            "float": 5.5,  # Will be converted to int
            "none": None,
            "empty": "",
        }
        # 10 + 20 + 5 (float to int) = 35
        assert MemberService._calculate_total(data) == 35

    def test_calculate_total_large_numbers(self):
        """Test total calculation with large numbers."""
        data = {"big": 999999999999, "also_big": 1}
        assert MemberService._calculate_total(data) == 1000000000000


@pytest.mark.django_db
class TestCalculationService:
    """Tests for CalculationService."""

    def test_calculate_group_totals(self, group_with_fields):
        """Test calculating group totals."""
        # Set up data
        for i, member in enumerate(group_with_fields.karma_members.all()):
            member.positive_total = 10 * (i + 1)
            member.negative_total = 5 * (i + 1)
            member.save()

        totals = CalculationService.calculate_group_totals(group_with_fields)

        assert totals["total_positive"] == 30  # 10 + 20
        assert totals["total_negative"] == 15  # 5 + 10
        assert totals["net_total"] == 15
        assert totals["member_count"] == 2

    def test_calculate_group_totals_single_member_no_data(self, user):
        """Test calculating totals for group with single member and no data."""
        group = GroupCreationModel.objects.create(user=user, title="Single", members_string="OnlyOne")
        member = group.karma_members.first()
        member.positive_total = 0
        member.negative_total = 0
        member.save()

        totals = CalculationService.calculate_group_totals(group)

        assert totals["total_positive"] == 0
        assert totals["total_negative"] == 0
        assert totals["net_total"] == 0
        assert totals["member_count"] == 1

    def test_calculate_group_totals_all_zeros(self, group_with_fields):
        """Test calculating totals when all values are zero."""
        for member in group_with_fields.karma_members.all():
            member.positive_total = 0
            member.negative_total = 0
            member.save()

        totals = CalculationService.calculate_group_totals(group_with_fields)

        assert totals["total_positive"] == 0
        assert totals["total_negative"] == 0
        assert totals["net_total"] == 0

    def test_calculate_group_totals_negative_net(self, group_with_fields):
        """Test calculating totals when negative exceeds positive."""
        for member in group_with_fields.karma_members.all():
            member.positive_total = 5
            member.negative_total = 20
            member.save()

        totals = CalculationService.calculate_group_totals(group_with_fields)

        assert totals["net_total"] == -30  # 10 - 40

    def test_get_member_ranking(self, group_with_fields):
        """Test getting member ranking."""
        members = list(group_with_fields.karma_members.all())
        members[0].positive_total = 20
        members[0].negative_total = 5
        members[0].save()
        members[1].positive_total = 10
        members[1].negative_total = 2
        members[1].save()

        ranking = CalculationService.get_member_ranking(group_with_fields)

        assert len(ranking) == 2
        # First should have higher net (20-5=15 vs 10-2=8)
        assert ranking[0]["net_total"] == 15
        assert ranking[0]["rank"] == 1
        assert ranking[1]["net_total"] == 8
        assert ranking[1]["rank"] == 2

    def test_get_member_ranking_by_positive(self, group_with_fields):
        """Test getting ranking ordered by positive total."""
        members = list(group_with_fields.karma_members.all())
        members[0].positive_total = 10
        members[0].save()
        members[1].positive_total = 20
        members[1].save()

        ranking = CalculationService.get_member_ranking(group_with_fields, order_by="positive")

        assert ranking[0]["positive_total"] == 20
        assert ranking[1]["positive_total"] == 10

    def test_get_member_ranking_by_negative(self, group_with_fields):
        """Test getting ranking ordered by negative total."""
        members = list(group_with_fields.karma_members.all())
        members[0].negative_total = 10
        members[0].save()
        members[1].negative_total = 20
        members[1].save()

        ranking = CalculationService.get_member_ranking(group_with_fields, order_by="negative")

        assert ranking[0]["negative_total"] == 20
        assert ranking[1]["negative_total"] == 10

    def test_get_member_ranking_includes_all_fields(self, group_with_fields):
        """Test that ranking includes all required fields."""
        ranking = CalculationService.get_member_ranking(group_with_fields)

        assert len(ranking) > 0
        for entry in ranking:
            assert "id" in entry
            assert "name" in entry
            assert "positive_total" in entry
            assert "negative_total" in entry
            assert "net_total" in entry
            assert "rank" in entry

    def test_get_member_ranking_tied_scores(self, group_with_fields):
        """Test ranking when members have tied scores."""
        for member in group_with_fields.karma_members.all():
            member.positive_total = 10
            member.negative_total = 5
            member.save()

        ranking = CalculationService.get_member_ranking(group_with_fields)

        # Both should have the same net_total
        assert ranking[0]["net_total"] == ranking[1]["net_total"]
        # But different ranks (no tie handling in current implementation)
        assert ranking[0]["rank"] == 1
        assert ranking[1]["rank"] == 2

    def test_recalculate_all_totals(self, group_with_fields):
        """Test recalculating all totals."""
        # Set up inconsistent data
        for member in group_with_fields.karma_members.all():
            member.positive_data = {"homework": 10}
            member.positive_total = 0  # Wrong!
            member.save()

        count = CalculationService.recalculate_all_totals(group_with_fields)

        assert count == 2
        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert member.positive_total == 10

    def test_recalculate_all_totals_with_text_fields(self, group_with_fields):
        """Test recalculating totals ignores text fields."""
        for member in group_with_fields.karma_members.all():
            member.positive_data = {"score": 10, "notes": "Good job"}
            member.positive_total = 999  # Wrong value
            member.save()

        CalculationService.recalculate_all_totals(group_with_fields)

        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert member.positive_total == 10  # Only numeric values counted

    def test_recalculate_all_totals_single_member(self, user):
        """Test recalculating totals for single member group."""
        group = GroupCreationModel.objects.create(user=user, title="Single", members_string="OnlyOne")

        count = CalculationService.recalculate_all_totals(group)
        assert count == 1


@pytest.mark.django_db
class TestServiceTransactions:
    """Tests for service transaction behavior."""

    def test_add_field_atomic(self, group_with_fields):
        """Test that add_field_to_members is atomic."""
        # This should succeed
        MemberService.add_field_to_members(
            group_with_fields,
            field_name="new_field",
            field_type="int",
            definition="positive",
        )

        # All members should have the field
        for member in group_with_fields.karma_members.all():
            assert "new_field" in member.positive_data

    def test_remove_field_atomic(self, group_with_fields):
        """Test that remove_field_from_members is atomic."""
        # Remove should affect all members and the FieldDefinition
        MemberService.remove_field_from_members(
            group_with_fields,
            field_name="homework",
            definition="positive",
        )

        # All members should be updated
        for member in group_with_fields.karma_members.all():
            assert "homework" not in member.positive_data

        # FieldDefinition should be deleted
        assert not FieldDefinition.objects.filter(group=group_with_fields, name="homework").exists()

    def test_rename_field_atomic(self, group_with_fields):
        """Test that rename_field_for_members is atomic."""
        for member in group_with_fields.karma_members.all():
            member.positive_data["homework"] = 50
            member.save()

        MemberService.rename_field_for_members(
            group_with_fields,
            old_name="homework",
            new_name="new_homework",
            definition="positive",
        )

        # All members should be updated
        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert "homework" not in member.positive_data
            assert member.positive_data["new_homework"] == 50


@pytest.mark.django_db
class TestServiceEdgeCases:
    """Edge case tests for services."""

    def test_update_member_with_none_values_in_data(self, group_with_fields):
        """Test updating member with None values in data dict."""
        member = group_with_fields.karma_members.first()
        MemberService.update_member_data(
            member,
            positive_data={"valid": 10, "null": None},
        )
        member.refresh_from_db()
        assert member.positive_data["valid"] == 10
        assert member.positive_data["null"] is None
        assert member.positive_total == 10  # None is ignored in total

    def test_add_field_to_single_member_group(self, user):
        """Test adding field to group with single member."""
        group = GroupCreationModel.objects.create(user=user, title="Single", members_string="Solo")
        MemberService.add_field_to_members(group, field_name="test", field_type="int", definition="positive")
        member = group.karma_members.first()
        assert "test" in member.positive_data

    def test_remove_field_with_empty_member_data(self, user):
        """Test removing field when member has empty data."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="A")
        member = group.karma_members.first()
        member.positive_data = {}
        member.save()

        # Should not raise
        MemberService.remove_field_from_members(group, field_name="test", definition="positive")

    def test_rename_field_not_in_member_data(self, group_with_fields):
        """Test renaming field that exists in FieldDefinition but not member data."""
        # Create FieldDefinition but don't add to members
        FieldDefinition.objects.create(
            group=group_with_fields,
            name="orphan_field",
            type="int",
            definition="positive",
        )

        # Should not raise
        MemberService.rename_field_for_members(
            group_with_fields,
            old_name="orphan_field",
            new_name="new_orphan",
            definition="positive",
        )

    def test_multiple_operations_sequence(self, group_with_fields):
        """Test sequence of multiple service operations."""
        # Add field
        MemberService.add_field_to_members(group_with_fields, "field1", "int", "positive")

        # Update data
        for member in group_with_fields.karma_members.all():
            MemberService.update_member_data(member, positive_data={**member.positive_data, "field1": 10})

        # Rename field
        MemberService.rename_field_for_members(group_with_fields, "field1", "renamed_field", "positive")

        # Verify
        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert member.positive_data.get("renamed_field") == 10

        # Remove field
        MemberService.remove_field_from_members(group_with_fields, "renamed_field", "positive")

        # Verify removal
        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert "renamed_field" not in member.positive_data

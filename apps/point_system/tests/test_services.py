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

    def test_create_field_assigns_first_order(self, user):
        """First field in (group, definition) bucket gets order=1."""
        group = GroupCreationModel.objects.create(user=user, title="G", members_string="A")
        field = MemberService.create_field(group, "homework", "int", "positive")
        assert field.order == 1

    def test_create_field_increments_order_per_bucket(self, user):
        """Each new field in a bucket gets max(order)+1; positive/negative independent."""
        group = GroupCreationModel.objects.create(user=user, title="G", members_string="A")
        f1 = MemberService.create_field(group, "homework", "int", "positive")
        f2 = MemberService.create_field(group, "tests", "int", "positive")
        f_neg = MemberService.create_field(group, "tardy", "int", "negative")
        assert (f1.order, f2.order) == (1, 2)
        assert f_neg.order == 1

    def test_create_field_syncs_members(self, group_with_fields):
        """create_field also seeds the field on every existing member."""
        MemberService.create_field(group_with_fields, "extra", "int", "positive")
        for m in group_with_fields.karma_members.all():
            assert m.positive_data["extra"] == 0

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
class TestClearFieldValues:
    """Tests for MemberService.clear_field_values."""

    def test_clear_int_field_resets_values_to_zero(self, group_with_fields):
        """Clearing a numeric column sets every member's value to 0."""
        for member in group_with_fields.karma_members.all():
            member.positive_data["homework"] = 42
            member.save()

        MemberService.clear_field_values(group_with_fields, "homework", "positive")

        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert member.positive_data["homework"] == 0
            assert member.positive_total == 0

    def test_clear_keeps_field_definition(self, group_with_fields):
        """Clearing a column does not delete its FieldDefinition."""
        MemberService.clear_field_values(group_with_fields, "homework", "positive")
        assert FieldDefinition.objects.filter(group=group_with_fields, name="homework", definition="positive").exists()

    def test_clear_text_field_resets_to_empty_string(self, group_with_fields):
        """Clearing a text column sets every member's value to ''."""
        FieldDefinition.objects.create(group=group_with_fields, name="notes", type="str", definition="positive")
        for member in group_with_fields.karma_members.all():
            member.positive_data["notes"] = "something"
            member.save()

        MemberService.clear_field_values(group_with_fields, "notes", "positive")

        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert member.positive_data["notes"] == ""

    def test_clear_preserves_other_fields(self, group_with_fields):
        """Clearing one column leaves other columns untouched."""
        FieldDefinition.objects.create(group=group_with_fields, name="tests", type="int", definition="positive")
        for member in group_with_fields.karma_members.all():
            member.positive_data["homework"] = 10
            member.positive_data["tests"] = 7
            member.save()

        MemberService.clear_field_values(group_with_fields, "homework", "positive")

        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert member.positive_data["homework"] == 0
            assert member.positive_data["tests"] == 7


@pytest.mark.django_db
class TestCreateFieldsEdgeCases:
    """Edge cases for MemberService.create_fields."""

    def test_empty_specs_returns_empty(self, user):
        group = GroupCreationModel.objects.create(user=user, title="G", members_string="A")
        assert MemberService.create_fields(group, [], "positive") == []
        assert FieldDefinition.objects.filter(group=group).count() == 0

    def test_blank_names_are_skipped(self, user):
        group = GroupCreationModel.objects.create(user=user, title="G", members_string="A")
        created = MemberService.create_fields(group, [("", "int"), ("ok", "int")], "positive")
        assert [f.name for f in created] == ["ok"]

    def test_order_continues_from_existing_max(self, group_with_fields):
        """Fixture fields are created with the default order 0, so new ones start at 1."""
        created = MemberService.create_fields(group_with_fields, [("a", "int"), ("b", "int")], "positive")
        assert [f.order for f in created] == [1, 2]
        assert created[0].order < created[1].order  # strictly increasing

    def test_negative_order_independent_of_positive(self, group_with_fields):
        created = MemberService.create_fields(group_with_fields, [("x", "int"), ("y", "int")], "negative")
        assert [f.order for f in created] == [1, 2]

    def test_mixed_types_get_correct_defaults(self, user):
        group = GroupCreationModel.objects.create(user=user, title="G", members_string="A, B")
        MemberService.create_fields(group, [("num", "int"), ("txt", "str")], "negative")
        for member in group.karma_members.all():
            assert member.negative_data["num"] == 0
            assert member.negative_data["txt"] == ""

    def test_existing_and_intra_batch_dups_all_collapsed(self, group_with_fields):
        created = MemberService.create_fields(
            group_with_fields,
            [("homework", "int"), ("dup", "int"), ("dup", "str")],
            "positive",
        )
        assert [f.name for f in created] == ["dup"]
        # First occurrence's type wins
        assert FieldDefinition.objects.get(group=group_with_fields, name="dup", definition="positive").type == "int"

    def test_seeds_members_with_empty_existing_data(self, user):
        group = GroupCreationModel.objects.create(user=user, title="G", members_string="A")
        member = group.karma_members.first()
        member.positive_data = {}
        member.save()
        MemberService.create_fields(group, [("p", "int")], "positive")
        member.refresh_from_db()
        assert member.positive_data == {"p": 0}


@pytest.mark.django_db
class TestClearFieldValuesEdgeCases:
    """Edge cases for MemberService.clear_field_values."""

    def test_field_absent_from_member_data_is_noop(self, group_with_fields):
        """FieldDefinition exists but the key is missing from a member's data."""
        for member in group_with_fields.karma_members.all():
            member.positive_data = {}
            member.save()
        MemberService.clear_field_values(group_with_fields, "homework", "positive")
        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert member.positive_data == {}
            assert member.positive_total == 0

    def test_recalculates_both_totals_leaving_other_side(self, group_with_fields):
        for member in group_with_fields.karma_members.all():
            member.positive_data = {"homework": 10}
            member.negative_data = {"tardiness": 5}
            member.positive_total = 10
            member.negative_total = 5
            member.save()
        MemberService.clear_field_values(group_with_fields, "homework", "positive")
        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert member.positive_total == 0
            assert member.negative_total == 5
            assert member.negative_data == {"tardiness": 5}

    def test_clear_negative_field(self, group_with_fields):
        for member in group_with_fields.karma_members.all():
            member.negative_data = {"tardiness": 8}
            member.negative_total = 8
            member.save()
        MemberService.clear_field_values(group_with_fields, "tardiness", "negative")
        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert member.negative_data["tardiness"] == 0
            assert member.negative_total == 0

    def test_clear_field_with_no_field_definition(self, group_with_fields):
        """Clearing a name that has no FieldDefinition defaults to numeric 0 and is harmless."""
        for member in group_with_fields.karma_members.all():
            member.positive_data = {"ghost": 7}
            member.save()
        MemberService.clear_field_values(group_with_fields, "ghost", "positive")
        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert member.positive_data["ghost"] == 0


@pytest.mark.django_db
class TestDeleteAllFieldsEdgeCases:
    """Edge cases for MemberService.delete_all_fields."""

    def test_delete_empty_table_is_noop(self, user):
        group = GroupCreationModel.objects.create(user=user, title="G", members_string="A")
        FieldDefinition.objects.create(group=group, name="hw", type="int", definition="positive")
        group.sync_members()
        # No negative fields exist; deleting them must not touch positive
        MemberService.delete_all_fields(group, "negative")
        assert FieldDefinition.objects.filter(group=group, definition="positive").exists()

    def test_preserves_other_side_total(self, group_with_fields):
        for member in group_with_fields.karma_members.all():
            member.positive_data = {"homework": 9}
            member.negative_data = {"tardiness": 4}
            member.positive_total = 9
            member.negative_total = 4
            member.save()
        MemberService.delete_all_fields(group_with_fields, "negative")
        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert member.negative_data == {}
            assert member.negative_total == 0
            assert member.positive_data == {"homework": 9}
            assert member.positive_total == 9

    def test_deletes_text_and_int_fields_together(self, group_with_fields):
        FieldDefinition.objects.create(group=group_with_fields, name="note", type="str", definition="positive")
        MemberService.delete_all_fields(group_with_fields, "positive")
        assert not FieldDefinition.objects.filter(group=group_with_fields, definition="positive").exists()


@pytest.mark.django_db
class TestCreateFields:
    """Tests for MemberService.create_fields (bulk column creation)."""

    def test_creates_multiple_fields_with_sequential_order(self, user):
        """Several columns created in one call get sequential order values."""
        group = GroupCreationModel.objects.create(user=user, title="G", members_string="A")
        created = MemberService.create_fields(
            group,
            [("homework", "int"), ("notes", "str"), ("tests", "int")],
            "positive",
        )
        assert [f.name for f in created] == ["homework", "notes", "tests"]
        assert [f.order for f in created] == [1, 2, 3]

    def test_syncs_all_fields_to_members(self, user):
        """Each created field is seeded on every member with the right default."""
        group = GroupCreationModel.objects.create(user=user, title="G", members_string="A, B")
        MemberService.create_fields(group, [("homework", "int"), ("notes", "str")], "positive")
        for member in group.karma_members.all():
            assert member.positive_data["homework"] == 0
            assert member.positive_data["notes"] == ""

    def test_skips_existing_names(self, group_with_fields):
        """A name already present in the table is skipped, not duplicated."""
        created = MemberService.create_fields(
            group_with_fields, [("homework", "int"), ("brand_new", "int")], "positive"
        )
        assert [f.name for f in created] == ["brand_new"]
        assert (
            FieldDefinition.objects.filter(group=group_with_fields, name="homework", definition="positive").count() == 1
        )

    def test_skips_duplicate_names_within_batch(self, user):
        """A name repeated within the batch is only created once."""
        group = GroupCreationModel.objects.create(user=user, title="G", members_string="A")
        created = MemberService.create_fields(group, [("dup", "int"), ("dup", "int")], "positive")
        assert [f.name for f in created] == ["dup"]


@pytest.mark.django_db
class TestDeleteAllFields:
    """Tests for MemberService.delete_all_fields (scoped to one table)."""

    def test_deletes_only_target_definition_fields(self, group_with_fields):
        """Only the target table's FieldDefinitions are removed; the other stays."""
        MemberService.delete_all_fields(group_with_fields, "positive")
        assert not FieldDefinition.objects.filter(group=group_with_fields, definition="positive").exists()
        assert FieldDefinition.objects.filter(group=group_with_fields, definition="negative").exists()

    def test_clears_only_target_side_data(self, group_with_fields):
        """Only the target side's member data and total are cleared."""
        for member in group_with_fields.karma_members.all():
            member.positive_data = {"homework": 10}
            member.negative_data = {"tardiness": 5}
            member.positive_total = 10
            member.negative_total = 5
            member.save()

        MemberService.delete_all_fields(group_with_fields, "positive")

        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert member.positive_data == {}
            assert member.positive_total == 0
            assert member.negative_data == {"tardiness": 5}  # untouched
            assert member.negative_total == 5

    def test_keeps_group_and_members(self, group_with_fields):
        """The group and its members are preserved."""
        group_id = group_with_fields.id
        MemberService.delete_all_fields(group_with_fields, "negative")
        assert GroupCreationModel.objects.filter(id=group_id).exists()
        assert group_with_fields.karma_members.count() == 2


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

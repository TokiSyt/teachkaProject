"""Tests for point_system app services."""

import pytest

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

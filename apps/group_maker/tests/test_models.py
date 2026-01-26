"""Tests for group_maker app models."""

import pytest

from apps.group_maker.models import GroupCreationModel

from .factories import GroupCreationModelFactory


@pytest.mark.django_db
class TestGroupCreationModel:
    """Tests for GroupCreationModel."""

    def test_create_group(self, user):
        """Test creating a group."""
        group = GroupCreationModel.objects.create(
            user=user,
            title="Test Group",
            members_string="Alice, Bob",
        )
        assert group.title == "Test Group"
        assert group.size == 2

    def test_get_members_list(self, group):
        """Test get_members_list returns correct list."""
        members = group.get_members_list()
        assert members == ["Alice", "Bob", "Charlie"]

    def test_get_members_list_strips_whitespace(self, user):
        """Test that whitespace is stripped from member names."""
        group = GroupCreationModel.objects.create(
            user=user,
            title="Test Group",
            members_string="  Alice  ,  Bob  ",
        )
        members = group.get_members_list()
        assert members == ["Alice", "Bob"]

    def test_get_members_list_handles_newlines(self, user):
        """Test that newlines are treated as separators."""
        group = GroupCreationModel.objects.create(
            user=user,
            title="Test Group",
            members_string="Alice\nBob\nCharlie",
        )
        members = group.get_members_list()
        assert members == ["Alice", "Bob", "Charlie"]

    def test_size_is_calculated_on_save(self, user):
        """Test that size is automatically calculated."""
        group = GroupCreationModel.objects.create(
            user=user,
            title="Test Group",
            members_string="A, B, C, D, E",
        )
        assert group.size == 5

    def test_empty_members_raises_error(self, user):
        """Test that empty members string raises ValueError."""
        with pytest.raises(ValueError, match="at least one member"):
            GroupCreationModel.objects.create(
                user=user,
                title="Empty Group",
                members_string="",
            )

    def test_factory_creates_valid_group(self):
        """Test that factory creates a valid group."""
        group = GroupCreationModelFactory()
        assert group.pk is not None
        assert group.user is not None
        assert group.size == 3  # Alice, Bob, Charlie


@pytest.mark.django_db
class TestGroupSignals:
    """Tests for group_maker signals."""

    def test_karma_members_created_on_save(self, user):
        """Test that karma members are created via signal."""
        group = GroupCreationModel.objects.create(
            user=user,
            title="Test Group",
            members_string="Alice, Bob",
        )
        # Signal should have created karma members
        assert group.karma_members.count() == 2
        assert set(group.karma_members.values_list("name", flat=True)) == {"Alice", "Bob"}

    def test_karma_members_synced_on_update(self, user):
        """Test that karma members are synced when group is updated."""
        group = GroupCreationModel.objects.create(
            user=user,
            title="Test Group",
            members_string="Alice, Bob",
        )
        # Update members
        group.members_string = "Alice, Charlie"
        group.save()

        # Bob should be removed, Charlie added
        member_names = set(group.karma_members.values_list("name", flat=True))
        assert member_names == {"Alice", "Charlie"}

import pytest

from apps.group_maker.models import GroupCreationModel
from apps.wheel.services.utils import choose_random_member


@pytest.mark.django_db
class TestChooseRandomMember:
    """Tests for choose_random_member service."""

    def test_returns_member_from_queryset(self, user):
        """Test that a member from the queryset is returned."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="Alice, Bob, Charlie")
        members = group.get_members()
        chosen, _ = choose_random_member(members, [])
        assert chosen in members

    def test_returns_updated_already_chosen_ids(self, user):
        """Test that chosen member's ID is added to already_chosen list."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="Alice, Bob, Charlie")
        members = group.get_members()
        chosen, already_chosen_ids = choose_random_member(members, [])
        assert chosen.id in already_chosen_ids

    def test_excludes_already_chosen_members(self, user):
        """Test that already chosen members are excluded."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="Alice, Bob, Charlie")
        members = group.get_members()
        alice = members.get(name="Alice")
        bob = members.get(name="Bob")
        already_chosen_ids = [alice.id, bob.id]

        chosen, _ = choose_random_member(members, already_chosen_ids)
        assert chosen.name == "Charlie"

    def test_returns_none_when_all_chosen(self, user):
        """Test that None is returned when all members have been chosen."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="Alice, Bob")
        members = group.get_members()
        all_ids = list(members.values_list("id", flat=True))

        chosen, returned_ids = choose_random_member(members, all_ids)
        assert chosen is None
        assert returned_ids == all_ids

    def test_single_member_group(self, user):
        """Test with a group containing only one member."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="Alice")
        members = group.get_members()
        chosen, already_chosen_ids = choose_random_member(members, [])
        assert chosen.name == "Alice"
        assert already_chosen_ids == [chosen.id]

    def test_appends_to_already_chosen_ids(self, user):
        """Test that new ID is appended to existing already_chosen list."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="Alice, Bob, Charlie")
        members = group.get_members()
        alice = members.get(name="Alice")
        already_chosen_ids = [alice.id]

        chosen, updated_ids = choose_random_member(members, already_chosen_ids)
        assert chosen.name in ["Bob", "Charlie"]
        assert len(updated_ids) == 2
        assert alice.id in updated_ids

    def test_handles_duplicate_names(self, user):
        """Test that duplicate names are treated as separate members."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="John, Alice, John")
        members = group.get_members()

        # Should have 3 members (2 Johns with different IDs)
        assert members.count() == 3

        john_members = members.filter(name="John")
        assert john_members.count() == 2

        # Each John should be choosable separately
        john1 = john_members.first()
        john1_id = john1.id

        # Pass a copy to avoid mutation affecting the assertion
        chosen, updated_ids = choose_random_member(members, [john1_id])

        # Should be able to choose John again (different ID) or Alice
        assert chosen is not None
        # The chosen member should NOT be john1 (already chosen)
        assert chosen.id != john1_id

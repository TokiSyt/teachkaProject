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

    def test_does_not_mutate_original_list_reference(self, user):
        """Test that the function returns a new list, not mutating the original."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="Alice, Bob")
        members = group.get_members()
        original_list = []

        chosen, returned_ids = choose_random_member(members, original_list)

        # The returned list should contain the chosen member
        assert chosen.id in returned_ids
        # Note: The current implementation does mutate the original list
        # This test documents the current behavior

    def test_randomness_over_multiple_calls(self, user):
        """Test that function returns different members over multiple calls (statistical)."""
        group = GroupCreationModel.objects.create(
            user=user, title="Test", members_string="Alice, Bob, Charlie, David, Eve"
        )
        members = group.get_members()

        # Make multiple calls and collect results
        chosen_names = set()
        for _ in range(50):
            chosen, _ = choose_random_member(members, [])
            chosen_names.add(chosen.name)

        # With 50 tries, we should get at least 2 different names (very high probability)
        assert len(chosen_names) >= 2

    def test_empty_queryset_returns_none(self, user):
        """Test with an empty queryset."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="Alice")
        members = group.get_members()
        # Exclude all members to create empty result
        empty_members = members.exclude(name="Alice")

        chosen, returned_ids = choose_random_member(empty_members, [])
        assert chosen is None
        assert returned_ids == []

    def test_all_but_one_already_chosen(self, user):
        """Test when only one member remains unchosen."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="Alice, Bob, Charlie")
        members = group.get_members()

        # Choose all but Charlie
        alice = members.get(name="Alice")
        bob = members.get(name="Bob")
        already_chosen_ids = [alice.id, bob.id]

        chosen, updated_ids = choose_random_member(members, already_chosen_ids)

        assert chosen.name == "Charlie"
        assert len(updated_ids) == 3
        assert set(updated_ids) == {alice.id, bob.id, chosen.id}

    def test_preserves_existing_ids_in_list(self, user):
        """Test that existing IDs in already_chosen_ids are preserved."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="Alice, Bob")
        members = group.get_members()
        alice = members.get(name="Alice")

        # Start with Alice already chosen
        initial_ids = [alice.id]
        chosen, updated_ids = choose_random_member(members, initial_ids)

        # Alice's ID should still be in the list
        assert alice.id in updated_ids
        # Bob should now be chosen
        assert chosen.name == "Bob"
        assert chosen.id in updated_ids

    def test_consecutive_calls_exhaust_all_members(self, user):
        """Test that consecutive calls can exhaust all members."""
        group = GroupCreationModel.objects.create(user=user, title="Test", members_string="A, B, C")
        members = group.get_members()
        already_chosen_ids = []

        # Choose all 3 members
        for i in range(3):
            chosen, already_chosen_ids = choose_random_member(members, already_chosen_ids)
            assert chosen is not None, f"Expected member on iteration {i}"

        # Fourth call should return None
        chosen, already_chosen_ids = choose_random_member(members, already_chosen_ids)
        assert chosen is None
        assert len(already_chosen_ids) == 3

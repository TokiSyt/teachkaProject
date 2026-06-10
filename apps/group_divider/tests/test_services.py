from apps.group_divider.services.group_split import group_split, group_split_by_teams


class TestGroupSplit:
    def test_splits_into_groups_of_size(self):
        members = ["A", "B", "C", "D", "E", "F"]
        result = group_split(members.copy(), 2)
        assert len(result) == 3
        assert all(len(group) == 2 for group in result)

    def test_handles_uneven_split(self):
        members = ["A", "B", "C", "D", "E"]
        result = group_split(members.copy(), 2)
        assert len(result) == 3
        # Last group may have fewer members
        assert len(result[-1]) <= 2

    def test_all_members_included(self):
        members = ["A", "B", "C", "D", "E"]
        result = group_split(members.copy(), 2)
        flat = [m for group in result for m in group]
        assert sorted(flat) == sorted(members)

    def test_single_group(self):
        members = ["A", "B", "C"]
        result = group_split(members.copy(), 3)
        assert len(result) == 1
        assert len(result[0]) == 3

    def test_group_size_larger_than_list(self):
        members = ["A", "B"]
        result = group_split(members.copy(), 5)
        assert len(result) == 1
        assert result[0] == ["A", "B"] or result[0] == ["B", "A"]

    def test_group_size_one(self):
        members = ["A", "B", "C"]
        result = group_split(members.copy(), 1)
        assert len(result) == 3
        assert all(len(group) == 1 for group in result)

    def test_shuffles_members(self):
        members = ["A", "B", "C", "D", "E", "F", "G", "H"]
        results = [group_split(members.copy(), 2) for _ in range(10)]
        # Check that not all results are the same (randomness)
        flat_results = [tuple(tuple(g) for g in r) for r in results]
        # With 8 members, very unlikely to get same order 10 times
        assert len(set(flat_results)) > 1


class TestGroupSplitByTeams:
    def test_creates_exact_number_of_teams(self):
        members = ["A", "B", "C", "D", "E", "F", "G"]
        result = group_split_by_teams(members.copy(), 3)
        assert len(result) == 3

    def test_distributes_evenly(self):
        members = ["A", "B", "C", "D", "E", "F"]
        result = group_split_by_teams(members.copy(), 3)
        assert all(len(team) == 2 for team in result)

    def test_uneven_distribution_off_by_one(self):
        members = ["A", "B", "C", "D", "E", "F", "G"]
        result = group_split_by_teams(members.copy(), 3)
        sizes = sorted(len(team) for team in result)
        assert sizes == [2, 2, 3]

    def test_all_members_included(self):
        members = ["A", "B", "C", "D", "E"]
        result = group_split_by_teams(members.copy(), 2)
        flat = [m for team in result for m in team]
        assert sorted(flat) == sorted(members)

    def test_more_teams_than_members_clamped(self):
        members = ["A", "B"]
        result = group_split_by_teams(members.copy(), 5)
        # No empty teams: clamp to member count
        assert len(result) == 2
        assert all(len(team) == 1 for team in result)

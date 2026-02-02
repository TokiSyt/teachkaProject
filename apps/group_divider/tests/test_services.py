from apps.group_divider.services.group_split import group_split


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

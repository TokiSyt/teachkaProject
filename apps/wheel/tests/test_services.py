from apps.wheel.services.utils import choose_a_random_name


class TestChooseRandomName:
    def test_returns_name_from_list(self):
        names = ["Alice", "Bob", "Charlie"]
        chosen, _ = choose_a_random_name(names, [])
        assert chosen in names

    def test_returns_updated_already_chosen(self):
        names = ["Alice", "Bob", "Charlie"]
        chosen, already_chosen = choose_a_random_name(names, [])
        assert chosen in already_chosen

    def test_excludes_already_chosen(self):
        names = ["Alice", "Bob", "Charlie"]
        already_chosen = ["Alice", "Bob"]
        chosen, _ = choose_a_random_name(names, already_chosen)
        assert chosen == "Charlie"

    def test_resets_when_all_chosen(self):
        names = ["Alice", "Bob"]
        already_chosen = ["Alice", "Bob"]
        chosen, new_already_chosen = choose_a_random_name(names, already_chosen)
        assert chosen in names
        assert len(new_already_chosen) == 1

    def test_single_name_list(self):
        names = ["Alice"]
        chosen, already_chosen = choose_a_random_name(names, [])
        assert chosen == "Alice"
        assert already_chosen == ["Alice"]

    def test_appends_to_already_chosen(self):
        names = ["Alice", "Bob", "Charlie"]
        already_chosen = ["Alice"]
        chosen, updated = choose_a_random_name(names, already_chosen)
        assert chosen in ["Bob", "Charlie"]
        assert len(updated) == 2
        assert "Alice" in updated

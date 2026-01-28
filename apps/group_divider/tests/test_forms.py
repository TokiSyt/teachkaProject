from apps.group_divider.forms import GroupMakerForm


class TestGroupMakerForm:
    def test_valid_data(self):
        form = GroupMakerForm(data={"size": 2})
        assert form.is_valid()

    def test_size_must_be_positive(self):
        form = GroupMakerForm(data={"size": 0})
        assert not form.is_valid()
        assert "size" in form.errors

    def test_negative_size_invalid(self):
        form = GroupMakerForm(data={"size": -1})
        assert not form.is_valid()
        assert "size" in form.errors

    def test_size_required(self):
        form = GroupMakerForm(data={})
        assert not form.is_valid()
        assert "size" in form.errors

    def test_size_one_is_valid(self):
        form = GroupMakerForm(data={"size": 1})
        assert form.is_valid()

    def test_large_size_is_valid(self):
        form = GroupMakerForm(data={"size": 100})
        assert form.is_valid()

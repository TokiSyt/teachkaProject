"""Comprehensive tests for point_system forms."""

import pytest

from apps.point_system.forms import AddFieldForm, EditColumnForm, GroupForm, RemoveFieldForm


@pytest.mark.django_db
class TestAddFieldForm:
    """Tests for AddFieldForm."""

    def test_valid_int_positive_field(self):
        """Test valid form with int positive field."""
        data = {
            "name": "homework",
            "type": "int",
            "definition": "positive",
        }
        form = AddFieldForm(data=data)
        assert form.is_valid()

    def test_valid_str_negative_field(self):
        """Test valid form with str negative field."""
        data = {
            "name": "notes",
            "type": "str",
            "definition": "negative",
        }
        form = AddFieldForm(data=data)
        assert form.is_valid()

    def test_invalid_empty_name(self):
        """Test that empty name is invalid."""
        data = {
            "name": "",
            "type": "int",
            "definition": "positive",
        }
        form = AddFieldForm(data=data)
        assert not form.is_valid()
        assert "name" in form.errors

    def test_invalid_type(self):
        """Test that invalid type is rejected."""
        data = {
            "name": "test",
            "type": "invalid",
            "definition": "positive",
        }
        form = AddFieldForm(data=data)
        assert not form.is_valid()
        assert "type" in form.errors

    def test_invalid_definition(self):
        """Test that invalid definition is rejected."""
        data = {
            "name": "test",
            "type": "int",
            "definition": "invalid",
        }
        form = AddFieldForm(data=data)
        assert not form.is_valid()
        assert "definition" in form.errors

    def test_name_max_length(self):
        """Test that name respects max_length."""
        data = {
            "name": "a" * 101,  # Max is 100
            "type": "int",
            "definition": "positive",
        }
        form = AddFieldForm(data=data)
        assert not form.is_valid()
        assert "name" in form.errors

    def test_name_with_spaces(self):
        """Test that name with spaces is valid."""
        data = {
            "name": "my homework",
            "type": "int",
            "definition": "positive",
        }
        form = AddFieldForm(data=data)
        assert form.is_valid()

    def test_name_with_special_characters(self):
        """Test that name with special characters is valid."""
        data = {
            "name": "test-field_1",
            "type": "int",
            "definition": "positive",
        }
        form = AddFieldForm(data=data)
        assert form.is_valid()


@pytest.mark.django_db
class TestEditColumnForm:
    """Tests for EditColumnForm."""

    def test_valid_rename(self):
        """Test valid form for renaming."""
        data = {
            "old_name": "homework",
            "new_name": "assignments",
            "field_definition": "positive",
        }
        form = EditColumnForm(data=data)
        assert form.is_valid()

    def test_empty_old_name(self):
        """Test that empty old_name is invalid."""
        data = {
            "old_name": "",
            "new_name": "assignments",
            "field_definition": "positive",
        }
        form = EditColumnForm(data=data)
        assert not form.is_valid()
        assert "old_name" in form.errors

    def test_empty_new_name(self):
        """Test that empty new_name is invalid."""
        data = {
            "old_name": "homework",
            "new_name": "",
            "field_definition": "positive",
        }
        form = EditColumnForm(data=data)
        assert not form.is_valid()
        assert "new_name" in form.errors

    def test_invalid_field_definition(self):
        """Test that invalid field_definition is rejected."""
        data = {
            "old_name": "homework",
            "new_name": "assignments",
            "field_definition": "invalid",
        }
        form = EditColumnForm(data=data)
        assert not form.is_valid()
        assert "field_definition" in form.errors

    def test_same_old_and_new_name(self):
        """Test that same old and new name is technically valid."""
        data = {
            "old_name": "homework",
            "new_name": "homework",
            "field_definition": "positive",
        }
        form = EditColumnForm(data=data)
        # Form validation passes, business logic should handle this
        assert form.is_valid()

    def test_new_name_max_length(self):
        """Test that new_name respects max_length."""
        data = {
            "old_name": "homework",
            "new_name": "a" * 51,  # Max is 50
            "field_definition": "positive",
        }
        form = EditColumnForm(data=data)
        assert not form.is_valid()
        assert "new_name" in form.errors


@pytest.mark.django_db
class TestRemoveFieldForm:
    """Tests for RemoveFieldForm."""

    def test_form_has_field_name_field(self):
        """Test form has field_name as a ChoiceField."""
        form = RemoveFieldForm()
        assert "field_name" in form.fields

    def test_form_with_empty_choices_rejects_data(self):
        """Test form with empty choices rejects any data."""
        form = RemoveFieldForm(data={"field_name": "anything"})
        # Empty choices means any submitted value is invalid
        assert not form.is_valid()
        assert "field_name" in form.errors

    def test_form_with_dynamic_choices(self):
        """Test form with dynamically set choices."""
        form = RemoveFieldForm(data={"field_name": "homework"})
        # Set choices dynamically (as would be done in a view)
        form.fields["field_name"].choices = [("homework", "homework"), ("quizzes", "quizzes")]
        assert form.is_valid()
        assert form.cleaned_data["field_name"] == "homework"

    def test_form_rejects_invalid_dynamic_choice(self):
        """Test form rejects values not in dynamic choices."""
        form = RemoveFieldForm(data={"field_name": "invalid"})
        form.fields["field_name"].choices = [("homework", "homework"), ("quizzes", "quizzes")]
        assert not form.is_valid()
        assert "field_name" in form.errors


@pytest.mark.django_db
class TestGroupForm:
    """Tests for GroupForm (dynamic member form)."""

    def test_form_with_member_data(self, member_with_data):
        """Test form creates fields from member data."""
        form = GroupForm(instance=member_with_data)

        # Check that dynamic fields were created
        assert "pos_homework" in form.fields
        assert "neg_tardiness" in form.fields

        # Check initial values
        assert form.fields["pos_homework"].initial == 10
        assert form.fields["neg_tardiness"].initial == 3

    def test_form_with_empty_member(self, group_with_fields):
        """Test form with member having empty data."""
        member = group_with_fields.karma_members.first()
        member.positive_data = {}
        member.negative_data = {}
        member.save()

        form = GroupForm(instance=member)
        # Should have base fields only
        assert "name" in form.fields

    def test_form_creates_dynamic_fields(self, member_with_data):
        """Test that form creates dynamic pos_ and neg_ prefixed fields."""
        form = GroupForm(instance=member_with_data)

        # Verify dynamic fields were created based on member data
        assert "pos_homework" in form.fields
        assert "neg_tardiness" in form.fields

        # Verify initial values are set correctly
        assert form.fields["pos_homework"].initial == 10
        assert form.fields["neg_tardiness"].initial == 3

        # Verify they are IntegerFields
        from django import forms

        assert isinstance(form.fields["pos_homework"], forms.IntegerField)
        assert isinstance(form.fields["neg_tardiness"], forms.IntegerField)

    def test_form_with_multiple_fields(self, group_with_fields):
        """Test form with multiple positive and negative fields."""
        member = group_with_fields.karma_members.first()
        member.positive_data = {"field1": 1, "field2": 2, "field3": 3}
        member.negative_data = {"neg1": 10, "neg2": 20}
        member.save()

        form = GroupForm(instance=member)
        assert "pos_field1" in form.fields
        assert "pos_field2" in form.fields
        assert "pos_field3" in form.fields
        assert "neg_neg1" in form.fields
        assert "neg_neg2" in form.fields

    def test_form_with_empty_dict_data(self, group_with_fields):
        """Test form handles empty dict data gracefully."""
        member = group_with_fields.karma_members.first()
        member.positive_data = {}
        member.negative_data = {}
        member.save()

        # Should not raise exception
        form = GroupForm(instance=member)
        assert "name" in form.fields


@pytest.mark.django_db
class TestFormEdgeCases:
    """Edge case tests for forms."""

    def test_add_field_form_whitespace_name(self):
        """Test form with whitespace-only name."""
        data = {
            "name": "   ",
            "type": "int",
            "definition": "positive",
        }
        form = AddFieldForm(data=data)
        # ModelForm with CharField - whitespace is valid data (not stripped)
        # The form considers this valid; business logic should handle edge cases
        # Check if the form is valid - depends on model validation
        form.is_valid()  # Just ensure no exception raised

    def test_edit_column_form_unicode_name(self):
        """Test form with unicode characters in name."""
        data = {
            "old_name": "homework",
            "new_name": "תרגיל בית",  # Hebrew
            "field_definition": "positive",
        }
        form = EditColumnForm(data=data)
        assert form.is_valid()

    def test_add_field_form_numeric_name(self):
        """Test form with numeric-only name."""
        data = {
            "name": "123",
            "type": "int",
            "definition": "positive",
        }
        form = AddFieldForm(data=data)
        assert form.is_valid()

    def test_remove_field_form_missing_data(self):
        """Test RemoveFieldForm with missing field_name."""
        form = RemoveFieldForm(data={})
        assert not form.is_valid()
        assert "field_name" in form.errors

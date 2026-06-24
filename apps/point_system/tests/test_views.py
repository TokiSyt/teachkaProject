"""Comprehensive tests for point_system views."""

import json

import pytest
from django.urls import reverse

from apps.group_maker.models import GroupCreationModel
from apps.point_system.models import FieldDefinition


@pytest.mark.django_db
class TestHomeView:
    """Tests for HomeView (karma-home)."""

    def test_home_view_requires_login(self, client):
        """Test that unauthenticated users are redirected."""
        url = reverse("karma:karma-home")
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_home_view_no_group_selected(self, authenticated_client):
        """Test home view without group selection."""
        url = reverse("karma:karma-home")
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert "groups" in response.context
        assert response.context["selected_group"] is None

    def test_home_view_with_group_selected(self, authenticated_client, group_with_fields):
        """Test home view with group selection."""
        url = reverse("karma:karma-home")
        response = authenticated_client.get(url, {"group_id": group_with_fields.id})
        assert response.status_code == 200
        assert response.context["selected_group"] == group_with_fields
        assert len(response.context["members"]) == 2

    def test_home_view_shows_columns(self, authenticated_client, group_with_fields):
        """Test that positive and negative columns are displayed."""
        url = reverse("karma:karma-home")
        response = authenticated_client.get(url, {"group_id": group_with_fields.id})
        assert "homework" in response.context["positive_data"]
        assert "tardiness" in response.context["negative_data"]

    def test_home_view_other_user_group_not_shown(self, authenticated_client, other_user):
        """Test that other user's groups are not shown."""
        # Create group for other user
        other_group = GroupCreationModel.objects.create(
            user=other_user,
            title="Other Group",
            members_string="X, Y",
        )
        url = reverse("karma:karma-home")
        response = authenticated_client.get(url)
        assert other_group not in response.context["groups"]

    def test_home_view_post_save_positive_data(self, authenticated_client, group_with_fields):
        """Test saving positive data via POST."""
        member = group_with_fields.karma_members.first()
        url = reverse("karma:karma-home")
        data = {
            "group_id": group_with_fields.id,
            "positive_save": "true",
            f"{member.id}_positive_homework": "25",
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 302
        member.refresh_from_db()
        # Values are sanitized to integers
        assert member.positive_data["homework"] == 25

    def test_home_view_post_save_negative_data(self, authenticated_client, group_with_fields):
        """Test saving negative data via POST."""
        member = group_with_fields.karma_members.first()
        url = reverse("karma:karma-home")
        data = {
            "group_id": group_with_fields.id,
            "negative_save": "true",
            f"{member.id}_negative_tardiness": "5",
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 302
        member.refresh_from_db()
        # Values are sanitized to integers
        assert member.negative_data["tardiness"] == 5

    def test_home_view_post_updates_totals(self, authenticated_client, group_with_fields):
        """Test that saving data updates totals correctly."""
        member = group_with_fields.karma_members.first()
        url = reverse("karma:karma-home")
        data = {
            "group_id": group_with_fields.id,
            "positive_save": "true",
            f"{member.id}_positive_homework": "10",
        }
        authenticated_client.post(url, data)
        member.refresh_from_db()
        assert member.positive_total == 10

    def test_home_view_post_multiple_members(self, authenticated_client, group_with_fields):
        """Test saving data for multiple members at once."""
        members = list(group_with_fields.karma_members.all())
        url = reverse("karma:karma-home")
        data = {
            "group_id": group_with_fields.id,
            "positive_save": "true",
            f"{members[0].id}_positive_homework": "10",
            f"{members[1].id}_positive_homework": "20",
        }
        authenticated_client.post(url, data)
        members[0].refresh_from_db()
        members[1].refresh_from_db()
        # Values are sanitized to integers
        assert members[0].positive_data["homework"] == 10
        assert members[1].positive_data["homework"] == 20

    def test_home_view_post_ignores_nonexistent_columns(self, authenticated_client, group_with_fields):
        """Test that POST ignores columns that don't exist in FieldDefinition."""
        member = group_with_fields.karma_members.first()
        url = reverse("karma:karma-home")
        data = {
            "group_id": group_with_fields.id,
            "positive_save": "true",
            f"{member.id}_positive_nonexistent": "999",
        }
        authenticated_client.post(url, data)
        member.refresh_from_db()
        assert "nonexistent" not in member.positive_data

    def test_home_view_visibility_defaults_true(self, authenticated_client, group_with_fields):
        """With no saved settings, both tables default to visible."""
        url = reverse("karma:karma-home")
        response = authenticated_client.get(url, {"group_id": group_with_fields.id})
        assert response.context["show_positive"] is True
        assert response.context["show_negative"] is True

    def test_home_view_visibility_reflects_saved(self, authenticated_client, group_with_fields):
        """Hidden table is reflected in context on next load."""
        from apps.point_system.models import PointSystemGroupSettings

        PointSystemGroupSettings.set_table_visibility(group_with_fields, "negative", False)
        url = reverse("karma:karma-home")
        response = authenticated_client.get(url, {"group_id": group_with_fields.id})
        assert response.context["show_negative"] is False
        assert response.context["show_positive"] is True

    def test_home_view_empty_groups(self, authenticated_client):
        """Test home view when user has no groups."""
        url = reverse("karma:karma-home")
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert len(response.context["groups"]) == 0


@pytest.mark.django_db
class TestAddColumnView:
    """Tests for AddColumn view (new-column)."""

    def test_add_column_requires_login(self, client, group_with_fields):
        """Test that unauthenticated users are redirected."""
        url = reverse("karma:new-column", args=[group_with_fields.id])
        response = client.get(url)
        assert response.status_code == 302

    def test_add_column_get(self, authenticated_client, group_with_fields):
        """Test GET request displays form."""
        url = reverse("karma:new-column", args=[group_with_fields.id])
        response = authenticated_client.get(url, {"table": "positive"})
        assert response.status_code == 200
        assert response.context["group_id"] == group_with_fields.id
        assert response.context["field_definition"] == "positive"

    def test_add_column_get_negative(self, authenticated_client, group_with_fields):
        """Test GET request for negative table."""
        url = reverse("karma:new-column", args=[group_with_fields.id])
        response = authenticated_client.get(url, {"table": "negative"})
        assert response.status_code == 200
        assert response.context["field_definition"] == "negative"

    def test_add_column_post_int_field(self, authenticated_client, group_with_fields):
        """Test adding a numerical column."""
        url = reverse("karma:new-column", args=[group_with_fields.id])
        data = {
            "name": "participation",
            "type": "int",
            "definition": "positive",
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 302  # Redirect on success

        # Verify FieldDefinition was created
        assert FieldDefinition.objects.filter(
            group=group_with_fields,
            name="participation",
            type="int",
            definition="positive",
        ).exists()

        # Verify field was added to all members
        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert "participation" in member.positive_data
            assert member.positive_data["participation"] == 0

    def test_add_column_post_str_field(self, authenticated_client, group_with_fields):
        """Test adding a text column."""
        url = reverse("karma:new-column", args=[group_with_fields.id])
        data = {
            "name": "notes",
            "type": "str",
            "definition": "negative",
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 302

        # Verify field was added with empty string default
        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert "notes" in member.negative_data
            assert member.negative_data["notes"] == ""

    def test_add_column_post_duplicate_name(self, authenticated_client, group_with_fields):
        """Test adding a column with duplicate name fails."""
        url = reverse("karma:new-column", args=[group_with_fields.id])
        data = {
            "name": "homework",  # Already exists in positive
            "type": "int",
            "definition": "positive",
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 200  # Returns to form with error
        # Should show error message
        assert "already exists" in str(response.content).lower()

    def test_add_column_same_name_different_table(self, authenticated_client, group_with_fields):
        """Test that same name can exist in different tables."""
        url = reverse("karma:new-column", args=[group_with_fields.id])
        data = {
            "name": "homework",  # Already exists in positive, but we add to negative
            "type": "int",
            "definition": "negative",
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 302  # Should succeed

    def test_add_column_other_user_group_404(self, authenticated_client, other_user):
        """Test adding column to other user's group returns 404."""
        other_group = GroupCreationModel.objects.create(
            user=other_user,
            title="Other Group",
            members_string="X",
        )
        url = reverse("karma:new-column", args=[other_group.id])
        response = authenticated_client.get(url, {"table": "positive"})
        assert response.status_code == 404

    def test_add_column_invalid_form(self, authenticated_client, group_with_fields):
        """Test adding column with invalid data."""
        url = reverse("karma:new-column", args=[group_with_fields.id])
        data = {
            "name": "",  # Empty name
            "type": "int",
            "definition": "positive",
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 200  # Returns to form

    def test_add_multiple_columns_at_once(self, authenticated_client, group_with_fields):
        """Posting parallel name/type lists creates one column per row."""
        url = reverse("karma:new-column", args=[group_with_fields.id])
        data = {
            "name": ["effort", "creativity", "notes"],
            "type": ["int", "int", "str"],
            "definition": "positive",
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 302

        for name in ["effort", "creativity", "notes"]:
            assert FieldDefinition.objects.filter(group=group_with_fields, name=name, definition="positive").exists()
        member = group_with_fields.karma_members.first()
        member.refresh_from_db()
        assert member.positive_data["effort"] == 0
        assert member.positive_data["notes"] == ""

    def test_add_multiple_columns_duplicate_rejected(self, authenticated_client, group_with_fields):
        """If any provided name already exists, the batch is rejected with an error."""
        url = reverse("karma:new-column", args=[group_with_fields.id])
        data = {
            "name": ["brand_new", "homework"],  # homework already exists
            "type": ["int", "int"],
            "definition": "positive",
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 200
        assert "already exists" in str(response.content).lower()
        # Nothing created
        assert not FieldDefinition.objects.filter(group=group_with_fields, name="brand_new").exists()

    def test_add_column_nonexistent_group(self, authenticated_client):
        """Test adding column to non-existent group returns 404."""
        url = reverse("karma:new-column", args=[99999])
        response = authenticated_client.get(url, {"table": "positive"})
        assert response.status_code == 404


@pytest.mark.django_db
class TestEditColumnView:
    """Tests for EditColumn view (edit-column)."""

    def test_edit_column_requires_login(self, client, group_with_fields):
        """Test that unauthenticated users are redirected."""
        url = reverse("karma:edit-column", args=[group_with_fields.id])
        response = client.get(url)
        assert response.status_code == 302

    def test_edit_column_get(self, authenticated_client, group_with_fields):
        """Test GET request displays form with columns."""
        url = reverse("karma:edit-column", args=[group_with_fields.id])
        response = authenticated_client.get(url, {"table": "positive"})
        assert response.status_code == 200
        assert "homework" in response.context["all_keys"]

    def test_edit_column_get_negative(self, authenticated_client, group_with_fields):
        """Test GET request for negative table."""
        url = reverse("karma:edit-column", args=[group_with_fields.id])
        response = authenticated_client.get(url, {"table": "negative"})
        assert response.status_code == 200
        assert "tardiness" in response.context["all_keys"]

    def test_edit_column_post_rename(self, authenticated_client, group_with_fields):
        """Test renaming a column."""
        # First set some data
        for member in group_with_fields.karma_members.all():
            member.positive_data["homework"] = 15
            member.save()

        url = reverse("karma:edit-column", args=[group_with_fields.id])
        data = {
            "old_name": "homework",
            "new_name": "assignments",
            "field_definition": "positive",
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 302  # Redirect on success

        # Verify FieldDefinition was renamed
        assert not FieldDefinition.objects.filter(group=group_with_fields, name="homework").exists()
        assert FieldDefinition.objects.filter(group=group_with_fields, name="assignments").exists()

        # Verify member data was renamed and preserved
        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert "homework" not in member.positive_data
            assert member.positive_data["assignments"] == 15

    def test_edit_column_post_duplicate_name(self, authenticated_client, group_with_fields):
        """Test renaming to an existing name fails."""
        # Add another field
        FieldDefinition.objects.create(
            group=group_with_fields,
            name="participation",
            type="int",
            definition="positive",
        )

        url = reverse("karma:edit-column", args=[group_with_fields.id])
        data = {
            "old_name": "homework",
            "new_name": "participation",  # Already exists
            "field_definition": "positive",
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 200  # Returns to form with error

    def test_edit_column_other_user_group_404(self, authenticated_client, other_user):
        """Test editing column in other user's group returns 404."""
        other_group = GroupCreationModel.objects.create(
            user=other_user,
            title="Other Group",
            members_string="X",
        )
        url = reverse("karma:edit-column", args=[other_group.id])
        response = authenticated_client.get(url, {"table": "positive"})
        assert response.status_code == 404

    def test_edit_column_shows_column_types(self, authenticated_client, group_with_fields):
        """Test that column types are shown in context."""
        url = reverse("karma:edit-column", args=[group_with_fields.id])
        response = authenticated_client.get(url, {"table": "positive"})
        assert "column_types" in response.context
        assert response.context["column_types"]["homework"] == "int"


@pytest.mark.django_db
class TestDeleteColumnView:
    """Tests for DeleteColumn view (delete-column)."""

    def test_delete_column_requires_login(self, client, group_with_fields):
        """Test that unauthenticated users are redirected."""
        url = reverse("karma:delete-column", args=[group_with_fields.id])
        response = client.get(url)
        assert response.status_code == 302

    def test_delete_column_get(self, authenticated_client, group_with_fields):
        """Test GET request displays columns to delete."""
        url = reverse("karma:delete-column", args=[group_with_fields.id])
        response = authenticated_client.get(url, {"table": "positive"})
        assert response.status_code == 200
        assert "homework" in response.context["all_keys"]

    def test_delete_column_get_negative(self, authenticated_client, group_with_fields):
        """Test GET request for negative table."""
        url = reverse("karma:delete-column", args=[group_with_fields.id])
        response = authenticated_client.get(url, {"table": "negative"})
        assert response.status_code == 200
        assert "tardiness" in response.context["all_keys"]

    def test_delete_column_post(self, authenticated_client, group_with_fields):
        """Test deleting a column."""
        url = reverse("karma:delete-column", args=[group_with_fields.id])
        data = {
            "field_name": "homework",
            "definition": "positive",
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 302  # Redirect on success

        # Verify FieldDefinition was deleted
        assert not FieldDefinition.objects.filter(group=group_with_fields, name="homework").exists()

        # Verify field was removed from all members
        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert "homework" not in member.positive_data

    def test_delete_column_post_invalid_field(self, authenticated_client, group_with_fields):
        """Test deleting a non-existent column."""
        url = reverse("karma:delete-column", args=[group_with_fields.id])
        data = {
            "field_name": "nonexistent",
            "definition": "positive",
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 200  # Returns to form

    def test_delete_column_other_user_group_404(self, authenticated_client, other_user):
        """Test deleting column in other user's group returns 404."""
        other_group = GroupCreationModel.objects.create(
            user=other_user,
            title="Other Group",
            members_string="X",
        )
        url = reverse("karma:delete-column", args=[other_group.id])
        response = authenticated_client.get(url, {"table": "positive"})
        assert response.status_code == 404

    def test_delete_column_removes_data(self, authenticated_client, group_with_fields):
        """Test that deleting a column removes all data."""
        # First set some data
        for member in group_with_fields.karma_members.all():
            member.positive_data["homework"] = 100
            member.positive_total = 100
            member.save()

        url = reverse("karma:delete-column", args=[group_with_fields.id])
        data = {
            "field_name": "homework",
            "definition": "positive",
        }
        authenticated_client.post(url, data)

        # Verify data was removed
        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert "homework" not in member.positive_data

    def test_delete_last_column(self, authenticated_client, user):
        """Test deleting the last column in a table."""
        group = GroupCreationModel.objects.create(
            user=user,
            title="Single Column Group",
            members_string="A, B",
        )
        FieldDefinition.objects.create(
            group=group,
            name="only_column",
            type="int",
            definition="positive",
        )
        group.sync_members()

        url = reverse("karma:delete-column", args=[group.id])
        data = {
            "field_name": "only_column",
            "definition": "positive",
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 302

        # Verify no positive fields remain
        assert not FieldDefinition.objects.filter(group=group, definition="positive").exists()


@pytest.mark.django_db
class TestClearColumnView:
    """Tests for ClearColumn view (clear-column)."""

    def test_clear_column_requires_login(self, client, group_with_fields):
        url = reverse("karma:clear-column", args=[group_with_fields.id])
        response = client.post(url, {"field_name": "homework", "definition": "positive"})
        assert response.status_code == 302
        assert "login" in response.url

    def test_clear_column_post_resets_values(self, authenticated_client, group_with_fields):
        for member in group_with_fields.karma_members.all():
            member.positive_data["homework"] = 30
            member.positive_total = 30
            member.save()

        url = reverse("karma:clear-column", args=[group_with_fields.id])
        response = authenticated_client.post(url, {"field_name": "homework", "definition": "positive"})
        assert response.status_code == 302

        for member in group_with_fields.karma_members.all():
            member.refresh_from_db()
            assert member.positive_data["homework"] == 0
            assert member.positive_total == 0
        # Column itself preserved
        assert FieldDefinition.objects.filter(group=group_with_fields, name="homework").exists()

    def test_clear_column_other_user_group_404(self, authenticated_client, other_user):
        other_group = GroupCreationModel.objects.create(user=other_user, title="Other", members_string="X")
        FieldDefinition.objects.create(group=other_group, name="hw", type="int", definition="positive")
        url = reverse("karma:clear-column", args=[other_group.id])
        response = authenticated_client.post(url, {"field_name": "hw", "definition": "positive"})
        assert response.status_code == 404


@pytest.mark.django_db
class TestDeleteAllColumnsView:
    """Tests for DeleteAllColumns view (delete-all-columns)."""

    def test_requires_login(self, client, group_with_fields):
        url = reverse("karma:delete-all-columns", args=[group_with_fields.id])
        response = client.post(url, {"definition": "positive"})
        assert response.status_code == 302
        assert "login" in response.url

    def test_deletes_only_target_table_keeps_group(self, authenticated_client, group_with_fields):
        url = reverse("karma:delete-all-columns", args=[group_with_fields.id])
        response = authenticated_client.post(url, {"definition": "positive"})
        assert response.status_code == 302
        # Only positive removed; negative table untouched
        assert not FieldDefinition.objects.filter(group=group_with_fields, definition="positive").exists()
        assert FieldDefinition.objects.filter(group=group_with_fields, definition="negative").exists()
        assert GroupCreationModel.objects.filter(id=group_with_fields.id).exists()
        assert group_with_fields.karma_members.count() == 2

    def test_other_user_group_404(self, authenticated_client, other_user):
        other_group = GroupCreationModel.objects.create(user=other_user, title="Other", members_string="X")
        url = reverse("karma:delete-all-columns", args=[other_group.id])
        response = authenticated_client.post(url, {"definition": "positive"})
        assert response.status_code == 404


@pytest.mark.django_db
class TestToggleTableView:
    """Tests for ToggleTable view (toggle-table)."""

    def test_requires_login(self, client, group_with_fields):
        url = reverse("karma:toggle-table", args=[group_with_fields.id])
        response = client.post(url, {"definition": "positive", "visible": "0"})
        assert response.status_code == 302
        assert "login" in response.url

    def test_hides_table_persists(self, authenticated_client, group_with_fields):
        from apps.point_system.models import PointSystemGroupSettings

        url = reverse("karma:toggle-table", args=[group_with_fields.id])
        response = authenticated_client.post(url, {"definition": "negative", "visible": "0"})
        assert response.status_code == 302
        settings = PointSystemGroupSettings.for_group(group_with_fields)
        assert settings.show_negative is False
        assert settings.show_positive is True

    def test_ajax_returns_204(self, authenticated_client, group_with_fields):
        url = reverse("karma:toggle-table", args=[group_with_fields.id])
        response = authenticated_client.post(
            url, {"definition": "positive", "visible": "0"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        assert response.status_code == 204

    def test_other_user_group_404(self, authenticated_client, other_user):
        other_group = GroupCreationModel.objects.create(user=other_user, title="Other", members_string="X")
        url = reverse("karma:toggle-table", args=[other_group.id])
        response = authenticated_client.post(url, {"definition": "positive", "visible": "0"})
        assert response.status_code == 404


@pytest.mark.django_db
class TestAddColumnMultiEdgeCases:
    """Edge cases for bulk column creation via the AddColumn view."""

    def test_more_names_than_types_extras_dropped(self, authenticated_client, group_with_fields):
        url = reverse("karma:new-column", args=[group_with_fields.id])
        data = {"name": ["a", "b", "c"], "type": ["int", "int"], "definition": "positive"}
        response = authenticated_client.post(url, data)
        assert response.status_code == 302
        assert FieldDefinition.objects.filter(group=group_with_fields, name="a").exists()
        assert FieldDefinition.objects.filter(group=group_with_fields, name="b").exists()
        assert not FieldDefinition.objects.filter(group=group_with_fields, name="c").exists()

    def test_whitespace_only_names_filtered(self, authenticated_client, group_with_fields):
        url = reverse("karma:new-column", args=[group_with_fields.id])
        data = {"name": ["   ", "good"], "type": ["int", "int"], "definition": "positive"}
        response = authenticated_client.post(url, data)
        assert response.status_code == 302
        assert FieldDefinition.objects.filter(group=group_with_fields, name="good").exists()
        assert (
            FieldDefinition.objects.filter(group=group_with_fields, definition="positive").count() == 2
        )  # homework + good

    def test_names_are_trimmed_before_save(self, authenticated_client, group_with_fields):
        url = reverse("karma:new-column", args=[group_with_fields.id])
        data = {"name": ["  Spaced  "], "type": ["int"], "definition": "positive"}
        authenticated_client.post(url, data)
        assert FieldDefinition.objects.filter(group=group_with_fields, name="Spaced").exists()

    def test_all_blank_rerenders_without_creating(self, authenticated_client, group_with_fields):
        url = reverse("karma:new-column", args=[group_with_fields.id])
        before = FieldDefinition.objects.filter(group=group_with_fields).count()
        data = {"name": ["", "  "], "type": ["int", "int"], "definition": "positive"}
        response = authenticated_client.post(url, data)
        assert response.status_code == 200
        assert FieldDefinition.objects.filter(group=group_with_fields).count() == before

    def test_invalid_definition_rerenders(self, authenticated_client, group_with_fields):
        url = reverse("karma:new-column", args=[group_with_fields.id])
        data = {"name": ["x"], "type": ["int"], "definition": "sideways"}
        response = authenticated_client.post(url, data)
        assert response.status_code == 200
        assert not FieldDefinition.objects.filter(group=group_with_fields, name="x").exists()

    def test_same_name_other_table_allowed_in_batch(self, authenticated_client, group_with_fields):
        """'homework' exists in positive; adding it to negative in a batch is fine."""
        url = reverse("karma:new-column", args=[group_with_fields.id])
        data = {"name": ["homework", "fresh"], "type": ["int", "int"], "definition": "negative"}
        response = authenticated_client.post(url, data)
        assert response.status_code == 302
        assert FieldDefinition.objects.filter(group=group_with_fields, name="homework", definition="negative").exists()


@pytest.mark.django_db
class TestClearColumnEdgeCases:
    """Edge cases for ClearColumn view."""

    def test_get_not_allowed(self, authenticated_client, group_with_fields):
        url = reverse("karma:clear-column", args=[group_with_fields.id])
        assert authenticated_client.get(url).status_code == 405

    def test_bogus_field_is_noop(self, authenticated_client, group_with_fields):
        member = group_with_fields.karma_members.first()
        member.positive_data = {"homework": 12}
        member.save()
        url = reverse("karma:clear-column", args=[group_with_fields.id])
        response = authenticated_client.post(url, {"field_name": "nope", "definition": "positive"})
        assert response.status_code == 302
        member.refresh_from_db()
        assert member.positive_data["homework"] == 12  # untouched

    def test_missing_definition_is_noop(self, authenticated_client, group_with_fields):
        member = group_with_fields.karma_members.first()
        member.positive_data = {"homework": 3}
        member.save()
        url = reverse("karma:clear-column", args=[group_with_fields.id])
        response = authenticated_client.post(url, {"field_name": "homework"})
        assert response.status_code == 302
        member.refresh_from_db()
        assert member.positive_data["homework"] == 3

    def test_clears_text_column(self, authenticated_client, group_with_fields):
        FieldDefinition.objects.create(group=group_with_fields, name="notes", type="str", definition="positive")
        member = group_with_fields.karma_members.first()
        member.positive_data["notes"] = "hello"
        member.save()
        url = reverse("karma:clear-column", args=[group_with_fields.id])
        authenticated_client.post(url, {"field_name": "notes", "definition": "positive"})
        member.refresh_from_db()
        assert member.positive_data["notes"] == ""


@pytest.mark.django_db
class TestDeleteAllColumnsEdgeCases:
    """Edge cases for DeleteAllColumns view."""

    def test_get_not_allowed(self, authenticated_client, group_with_fields):
        url = reverse("karma:delete-all-columns", args=[group_with_fields.id])
        assert authenticated_client.get(url).status_code == 405

    def test_invalid_definition_deletes_nothing(self, authenticated_client, group_with_fields):
        url = reverse("karma:delete-all-columns", args=[group_with_fields.id])
        response = authenticated_client.post(url, {"definition": "bogus"})
        assert response.status_code == 302
        assert FieldDefinition.objects.filter(group=group_with_fields).count() == 2

    def test_missing_definition_deletes_nothing(self, authenticated_client, group_with_fields):
        url = reverse("karma:delete-all-columns", args=[group_with_fields.id])
        response = authenticated_client.post(url, {})
        assert response.status_code == 302
        assert FieldDefinition.objects.filter(group=group_with_fields).count() == 2


@pytest.mark.django_db
class TestToggleTableEdgeCases:
    """Edge cases for ToggleTable view."""

    def test_get_not_allowed(self, authenticated_client, group_with_fields):
        url = reverse("karma:toggle-table", args=[group_with_fields.id])
        assert authenticated_client.get(url).status_code == 405

    def test_invalid_definition_creates_no_settings(self, authenticated_client, group_with_fields):
        from apps.point_system.models import PointSystemGroupSettings

        url = reverse("karma:toggle-table", args=[group_with_fields.id])
        response = authenticated_client.post(url, {"definition": "bogus", "visible": "0"})
        assert response.status_code == 302
        assert not PointSystemGroupSettings.objects.filter(group=group_with_fields).exists()

    def test_visible_omitted_hides_table(self, authenticated_client, group_with_fields):
        from apps.point_system.models import PointSystemGroupSettings

        url = reverse("karma:toggle-table", args=[group_with_fields.id])
        authenticated_client.post(url, {"definition": "positive"})
        assert PointSystemGroupSettings.for_group(group_with_fields).show_positive is False

    def test_show_after_hide_round_trips(self, authenticated_client, group_with_fields):
        from apps.point_system.models import PointSystemGroupSettings

        url = reverse("karma:toggle-table", args=[group_with_fields.id])
        authenticated_client.post(url, {"definition": "negative", "visible": "0"})
        authenticated_client.post(url, {"definition": "negative", "visible": "1"})
        assert PointSystemGroupSettings.for_group(group_with_fields).show_negative is True

    def test_home_get_creates_settings_row(self, authenticated_client, group_with_fields):
        from apps.point_system.models import PointSystemGroupSettings

        assert not PointSystemGroupSettings.objects.filter(group=group_with_fields).exists()
        authenticated_client.get(reverse("karma:karma-home"), {"group_id": group_with_fields.id})
        assert PointSystemGroupSettings.objects.filter(group=group_with_fields).exists()


@pytest.mark.django_db
class TestViewIntegration:
    """Integration tests for view workflows."""

    def test_full_column_lifecycle(self, authenticated_client, user):
        """Test complete workflow: create group -> add column -> edit -> delete."""
        # Create group
        group = GroupCreationModel.objects.create(
            user=user,
            title="Integration Test Group",
            members_string="Alice, Bob, Charlie",
        )

        # Add a column
        add_url = reverse("karma:new-column", args=[group.id])
        authenticated_client.post(
            add_url,
            {
                "name": "test_column",
                "type": "int",
                "definition": "positive",
            },
        )

        # Verify column was added
        assert FieldDefinition.objects.filter(group=group, name="test_column").exists()
        for member in group.karma_members.all():
            assert "test_column" in member.positive_data

        # Save some data
        home_url = reverse("karma:karma-home")
        member = group.karma_members.first()
        authenticated_client.post(
            home_url,
            {
                "group_id": group.id,
                "positive_save": "true",
                f"{member.id}_positive_test_column": "50",
            },
        )
        member.refresh_from_db()
        # Values are sanitized to integers
        assert member.positive_data["test_column"] == 50

        # Rename column
        edit_url = reverse("karma:edit-column", args=[group.id])
        authenticated_client.post(
            edit_url,
            {
                "old_name": "test_column",
                "new_name": "renamed_column",
                "field_definition": "positive",
            },
        )

        # Verify rename preserved data
        member.refresh_from_db()
        assert "test_column" not in member.positive_data
        # Value stays as integer after rename
        assert member.positive_data["renamed_column"] == 50

        # Delete column
        delete_url = reverse("karma:delete-column", args=[group.id])
        authenticated_client.post(
            delete_url,
            {
                "field_name": "renamed_column",
                "definition": "positive",
            },
        )

        # Verify column was deleted
        assert not FieldDefinition.objects.filter(group=group, name="renamed_column").exists()
        member.refresh_from_db()
        assert "renamed_column" not in member.positive_data

    def test_multiple_columns_same_group(self, authenticated_client, user):
        """Test adding multiple columns to the same group."""
        group = GroupCreationModel.objects.create(
            user=user,
            title="Multi Column Group",
            members_string="A, B",
        )

        add_url = reverse("karma:new-column", args=[group.id])

        # Add multiple positive columns
        for name in ["homework", "quizzes", "participation"]:
            authenticated_client.post(
                add_url,
                {
                    "name": name,
                    "type": "int",
                    "definition": "positive",
                },
            )

        # Add multiple negative columns
        for name in ["tardiness", "missing_work"]:
            authenticated_client.post(
                add_url,
                {
                    "name": name,
                    "type": "int",
                    "definition": "negative",
                },
            )

        # Verify all columns exist
        assert FieldDefinition.objects.filter(group=group, definition="positive").count() == 3
        assert FieldDefinition.objects.filter(group=group, definition="negative").count() == 2

        # Verify all members have all columns
        for member in group.karma_members.all():
            assert len(member.positive_data) == 3
            assert len(member.negative_data) == 2

    def test_text_and_int_columns_mixed(self, authenticated_client, user):
        """Test mixing text and numerical columns."""
        group = GroupCreationModel.objects.create(
            user=user,
            title="Mixed Type Group",
            members_string="A",
        )

        add_url = reverse("karma:new-column", args=[group.id])

        # Add int column
        authenticated_client.post(
            add_url,
            {
                "name": "score",
                "type": "int",
                "definition": "positive",
            },
        )

        # Add str column
        authenticated_client.post(
            add_url,
            {
                "name": "notes",
                "type": "str",
                "definition": "positive",
            },
        )

        member = group.karma_members.first()
        assert member.positive_data["score"] == 0
        assert member.positive_data["notes"] == ""

        # Save data
        home_url = reverse("karma:karma-home")
        authenticated_client.post(
            home_url,
            {
                "group_id": group.id,
                "positive_save": "true",
                f"{member.id}_positive_score": "100",
                f"{member.id}_positive_notes": "Great work!",
            },
        )

        member.refresh_from_db()
        # Numeric values are sanitized to integers
        assert member.positive_data["score"] == 100
        # Text values remain as strings
        assert member.positive_data["notes"] == "Great work!"
        # Total should only count numerical
        assert member.positive_total == 100


@pytest.mark.django_db
class TestColumnReorderView:
    """Tests for column reorder endpoint."""

    def _make_fields(self, group, definition="positive"):
        f1 = FieldDefinition.objects.create(group=group, name="a", type="int", definition=definition, order=1)
        f2 = FieldDefinition.objects.create(group=group, name="b", type="int", definition=definition, order=2)
        f3 = FieldDefinition.objects.create(group=group, name="c", type="int", definition=definition, order=3)
        return f1, f2, f3

    def test_persists_new_order(self, authenticated_client, user):
        group = GroupCreationModel.objects.create(user=user, title="G", members_string="A")
        f1, f2, f3 = self._make_fields(group, "positive")
        url = reverse("karma:column-reorder", kwargs={"group_pk": group.id})
        resp = authenticated_client.post(
            url,
            data=json.dumps({"definition": "positive", "order": [f3.pk, f1.pk, f2.pk]}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        f1.refresh_from_db()
        f2.refresh_from_db()
        f3.refresh_from_db()
        assert (f3.order, f1.order, f2.order) == (1, 2, 3)

    def test_rejects_id_set_mismatch(self, authenticated_client, user):
        group = GroupCreationModel.objects.create(user=user, title="G", members_string="A")
        f1, _, _ = self._make_fields(group, "positive")
        url = reverse("karma:column-reorder", kwargs={"group_pk": group.id})
        resp = authenticated_client.post(
            url,
            data=json.dumps({"definition": "positive", "order": [f1.pk, 999999]}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_scoped_to_definition(self, authenticated_client, user):
        """Reordering positive does not touch negative."""
        group = GroupCreationModel.objects.create(user=user, title="G", members_string="A")
        p1, p2, p3 = self._make_fields(group, "positive")
        n1 = FieldDefinition.objects.create(group=group, name="x", type="int", definition="negative", order=1)
        n2 = FieldDefinition.objects.create(group=group, name="y", type="int", definition="negative", order=2)
        url = reverse("karma:column-reorder", kwargs={"group_pk": group.id})
        authenticated_client.post(
            url,
            data=json.dumps({"definition": "positive", "order": [p3.pk, p2.pk, p1.pk]}),
            content_type="application/json",
        )
        n1.refresh_from_db()
        n2.refresh_from_db()
        assert (n1.order, n2.order) == (1, 2)

    def test_rejects_other_user_group(self, authenticated_client, other_user):
        group = GroupCreationModel.objects.create(user=other_user, title="G", members_string="A")
        FieldDefinition.objects.create(group=group, name="a", type="int", definition="positive", order=1)
        url = reverse("karma:column-reorder", kwargs={"group_pk": group.id})
        resp = authenticated_client.post(
            url,
            data=json.dumps({"definition": "positive", "order": []}),
            content_type="application/json",
        )
        assert resp.status_code == 404


@pytest.mark.django_db
class TestKarmaDashboardView:
    """Tests for DashboardView (karma-dashboard, member deep-dive #59)."""

    def test_owner_get_returns_200_with_member(self, authenticated_client, member_with_data):
        url = reverse("karma:karma-dashboard", args=[member_with_data.id])
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert response.context["member"] == member_with_data
        assert response.context["net"] == 7
        assert member_with_data.name in response.content.decode()

    def test_non_owner_get_returns_404(self, client, other_user, member_with_data):
        client.force_login(other_user)
        url = reverse("karma:karma-dashboard", args=[member_with_data.id])
        assert client.get(url).status_code == 404

    def test_nonexistent_member_returns_404(self, authenticated_client):
        url = reverse("karma:karma-dashboard", args=[999999])
        assert authenticated_client.get(url).status_code == 404

    def test_requires_login(self, client, member_with_data):
        url = reverse("karma:karma-dashboard", args=[member_with_data.id])
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_renders_three_tabs_negative_default(self, authenticated_client, member_with_data):
        url = reverse("karma:karma-dashboard", args=[member_with_data.id])
        html = authenticated_client.get(url).content.decode()
        assert 'aria-label="Positive"' in html
        assert 'aria-label="Negative"' in html
        assert 'aria-label="Notes"' in html
        assert 'data-default-tab="negative"' in html

    def test_legend_shows_column_name_and_value(self, authenticated_client, member_with_data):
        # Negative tab is default; tardiness=3 should appear in its legend.
        url = reverse("karma:karma-dashboard", args=[member_with_data.id])
        html = authenticated_client.get(url).content.decode()
        assert "tardiness" in html

    def test_all_zero_shows_no_values_yet(self, authenticated_client, member_with_data):
        member_with_data.positive_data = {"homework": 0}
        member_with_data.negative_data = {"tardiness": 0}
        member_with_data.save()
        url = reverse("karma:karma-dashboard", args=[member_with_data.id])
        html = authenticated_client.get(url).content.decode()
        assert "No values yet" in html

    def test_no_columns_shows_add_cta(self, authenticated_client, user):
        from apps.group_maker.models import GroupCreationModel
        group = GroupCreationModel.objects.create(user=user, title="Bare", members_string="Solo")
        member = group.karma_members.first()
        url = reverse("karma:karma-dashboard", args=[member.id])
        html = authenticated_client.get(url).content.decode()
        cta = reverse("karma:new-column", args=[group.id])
        assert cta in html

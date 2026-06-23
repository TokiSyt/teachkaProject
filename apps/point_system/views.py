import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError, transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import TemplateView

from apps.group_maker.models import GroupCreationModel

from .forms import EditColumnForm
from .models import FieldDefinition, PointSystemGroupSettings
from .selectors import get_group_full_data, get_group_with_members, get_user_groups
from .services.member_service import MemberService


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "point_system/home.html"

    def get_context_data(self, group_id=None):
        """Build context using selectors."""
        context = {
            "groups": get_user_groups(self.request.user),
            "selected_group": None,
            "group_id": group_id,
            "members": [],
            "positive_data": [],
            "negative_data": [],
            "column_type_positive": {},
            "column_type_negative": {},
            "positive_fields": [],
            "negative_fields": [],
            "show_positive": True,
            "show_negative": True,
        }

        if group_id:
            try:
                data = get_group_full_data(int(group_id), self.request.user)
            except (TypeError, ValueError):
                return context
            settings = PointSystemGroupSettings.for_group(data["group"])
            context.update(
                {
                    "selected_group": data["group"],
                    "members": data["members"],
                    "positive_data": data["positive_column_names"],
                    "negative_data": data["negative_column_names"],
                    "column_type_positive": data["column_type_positive"],
                    "column_type_negative": data["column_type_negative"],
                    "positive_fields": data["positive_fields"],
                    "negative_fields": data["negative_fields"],
                    "show_positive": settings.show_positive,
                    "show_negative": settings.show_negative,
                }
            )

        return context

    def get(self, request):
        group_id = request.GET.get("group_id")
        context = self.get_context_data(group_id)
        return render(request, self.template_name, context)

    def post(self, request):
        group_id = request.POST.get("group_id")
        if not group_id:
            return redirect(reverse("karma:karma-home"))
        try:
            _, members = get_group_with_members(int(group_id), request.user)
        except (TypeError, ValueError):
            return redirect(reverse("karma:karma-home"))

        # Pre-index POST data by member ID in a single pass: O(m) instead of O(n*m)
        post_data = {}
        for key, value in request.POST.items():
            for sep in ("_positive_", "_negative_"):
                if sep in key:
                    member_id, col_name = key.split(sep, 1)
                    kind = sep.strip("_")  # "positive" or "negative"
                    post_data.setdefault(member_id, {}).setdefault(kind, {})[col_name] = value
                    break

        for member in members:
            member_post = post_data.get(str(member.id), {})

            if "negative_save" in request.POST:
                negative_data = member.negative_data.copy() if member.negative_data else {}
                for col_name, value in member_post.get("negative", {}).items():
                    if col_name in negative_data:
                        negative_data[col_name] = value
                MemberService.update_member_data(member, negative_data=negative_data)
            elif "positive_save" in request.POST:
                positive_data = member.positive_data.copy() if member.positive_data else {}
                for col_name, value in member_post.get("positive", {}).items():
                    if col_name in positive_data:
                        positive_data[col_name] = value
                MemberService.update_member_data(member, positive_data=positive_data)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return HttpResponse(status=204)
        return redirect(f"{reverse('karma:karma-home')}?group_id={group_id}")


class AddColumn(LoginRequiredMixin, TemplateView):
    template_name = "point_system/new_column.html"

    def get(self, request, pk):
        group = get_object_or_404(GroupCreationModel, id=pk, user=request.user)
        field_definition = request.GET.get("table")
        return render(
            request,
            self.template_name,
            {
                "group_id": group.id,
                "field_definition": field_definition,
            },
        )

    def post(self, request, pk):
        group = get_object_or_404(GroupCreationModel, id=pk, user=request.user)
        field_definition = request.POST.get("definition")

        # Collect one or more (name, type) rows. Single-row submissions arrive as
        # one-element lists, so the same path handles both cases.
        names = request.POST.getlist("name")
        types = request.POST.getlist("type")
        specs = [(name.strip(), ftype) for name, ftype in zip(names, types, strict=False) if name.strip()]

        def _rerender():
            return render(
                request,
                self.template_name,
                {"group_id": group.id, "field_definition": field_definition},
            )

        if field_definition not in ("positive", "negative") or not specs:
            return _rerender()

        existing = set(
            FieldDefinition.objects.filter(group=group, definition=field_definition).values_list("name", flat=True)
        )
        duplicates = [name for name, _ in specs if name in existing]
        if duplicates:
            messages.error(
                request,
                _("A column named '%(name)s' already exists in %(definition)s table.")
                % {"name": duplicates[0], "definition": field_definition},
            )
            return _rerender()

        MemberService.create_fields(group, specs, field_definition)
        return redirect(f"{reverse('karma:karma-home')}?group_id={group.id}")


def _get_field_data(group, table_definition):
    """Get field names and types for the given table definition (positive/negative)."""
    fields = list(FieldDefinition.objects.filter(group=group, definition=table_definition).values_list("name", "type"))
    all_keys = [f[0] for f in fields]
    column_types = {f[0]: f[1] for f in fields}
    return all_keys, column_types


class EditColumn(LoginRequiredMixin, TemplateView):
    template_name = "point_system/edit_column.html"

    def get(self, request, pk):
        group = get_object_or_404(GroupCreationModel, id=pk, user=request.user)
        table_definition = request.GET.get("table")  # "positive" or "negative"
        all_keys, column_types = _get_field_data(group, table_definition)

        return render(
            request,
            self.template_name,
            {
                "group_id": group.id,
                "all_keys": all_keys,
                "column_types": column_types,
                "table_definition": table_definition,
            },
        )

    def post(self, request, pk):
        group = get_object_or_404(GroupCreationModel, id=pk, user=request.user)
        table_definition = request.POST.get("field_definition")
        form = EditColumnForm(request.POST)
        all_keys, column_types = _get_field_data(group, table_definition)

        if form.is_valid():
            new_name = form.cleaned_data["new_name"]
            old_name = form.cleaned_data["old_name"]

            try:
                # Use service to rename field
                MemberService.rename_field_for_members(group, old_name, new_name, table_definition)
                return redirect(f"{reverse('karma:karma-home')}?group_id={group.id}")

            except FieldDefinition.DoesNotExist:
                messages.error(request, _("Column '%(name)s' not found.") % {"name": old_name})

            except IntegrityError:
                messages.error(request, _("A column named '%(name)s' already exists.") % {"name": new_name})

        return render(
            request,
            self.template_name,
            {
                "group_id": group.id,
                "all_keys": all_keys,
                "column_types": column_types,
                "table_definition": table_definition,
                "form": form,
            },
        )


class DeleteColumn(LoginRequiredMixin, TemplateView):
    template_name = "point_system/delete_column.html"

    def get(self, request, pk):
        group = get_object_or_404(GroupCreationModel, id=pk, user=request.user)
        table_definition = request.GET.get("table")  # "positive" or "negative"
        all_keys, column_types = _get_field_data(group, table_definition)

        return render(
            request,
            self.template_name,
            {
                "group_id": group.id,
                "all_keys": all_keys,
                "column_types": column_types,
                "table_definition": table_definition,
            },
        )

    def post(self, request, pk):
        group = get_object_or_404(GroupCreationModel, id=pk, user=request.user)
        table_definition = request.POST.get("definition")
        field_name = request.POST.get("field_name")

        all_keys, column_types = _get_field_data(group, table_definition)

        if field_name and field_name in all_keys:
            # Use service to remove field
            MemberService.remove_field_from_members(group, field_name, table_definition)

            return redirect(f"{reverse('karma:karma-home')}?group_id={group.id}")

        return render(
            request,
            self.template_name,
            {
                "group_id": group.id,
                "all_keys": all_keys,
                "column_types": column_types,
                "table_definition": table_definition,
            },
        )


class ClearColumn(LoginRequiredMixin, View):
    """Reset every member's value for a single column, keeping the column."""

    def post(self, request, pk):
        group = get_object_or_404(GroupCreationModel, id=pk, user=request.user)
        definition = request.POST.get("definition")
        field_name = request.POST.get("field_name")
        all_keys, _ = _get_field_data(group, definition)
        if field_name and field_name in all_keys:
            MemberService.clear_field_values(group, field_name, definition)
        return redirect(f"{reverse('karma:karma-home')}?group_id={group.id}")


class DeleteAllColumns(LoginRequiredMixin, View):
    """Delete every column from a group without deleting the group itself."""

    def post(self, request, pk):
        group = get_object_or_404(GroupCreationModel, id=pk, user=request.user)
        definition = request.POST.get("definition")
        if definition in ("positive", "negative"):
            MemberService.delete_all_fields(group, definition)
        return redirect(f"{reverse('karma:karma-home')}?group_id={group.id}")


class ToggleTable(LoginRequiredMixin, View):
    """Persist whether a group's positive or negative table is shown."""

    def post(self, request, pk):
        group = get_object_or_404(GroupCreationModel, id=pk, user=request.user)
        definition = request.POST.get("definition")
        if definition in ("positive", "negative"):
            visible = request.POST.get("visible") == "1"
            PointSystemGroupSettings.set_table_visibility(group, definition, visible)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return HttpResponse(status=204)
        return redirect(f"{reverse('karma:karma-home')}?group_id={group.id}")


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "wip.html"


class ColumnReorderView(LoginRequiredMixin, View):
    """Persist a new column order for a group's positive or negative fields."""

    def post(self, request, group_pk):
        group = get_object_or_404(GroupCreationModel, id=group_pk, user=request.user)
        try:
            payload = json.loads(request.body or b"{}")
            definition = payload.get("definition")
            ids = [int(x) for x in payload.get("order", [])]
        except (ValueError, TypeError):
            return JsonResponse({"ok": False, "error": "bad payload"}, status=400)

        if definition not in ("positive", "negative"):
            return JsonResponse({"ok": False, "error": "bad definition"}, status=400)

        valid_ids = set(FieldDefinition.objects.filter(group=group, definition=definition).values_list("pk", flat=True))
        if set(ids) != valid_ids:
            return JsonResponse({"ok": False, "error": "id mismatch"}, status=400)

        with transaction.atomic():
            for index, field_pk in enumerate(ids, start=1):
                FieldDefinition.objects.filter(pk=field_pk, group=group, definition=definition).update(order=index)
        return JsonResponse({"ok": True})

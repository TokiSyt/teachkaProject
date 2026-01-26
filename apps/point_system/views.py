from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import TemplateView

from apps.group_maker.models import GroupCreationModel

from .forms import AddFieldForm, EditColumnForm, RemoveFieldForm
from .models import FieldDefinition
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
        }

        if group_id:
            data = get_group_full_data(int(group_id), self.request.user)
            context.update({
                "selected_group": data["group"],
                "members": data["members"],
                "positive_data": data["positive_column_names"],
                "negative_data": data["negative_column_names"],
                "column_type_positive": data["column_type_positive"],
                "column_type_negative": data["column_type_negative"],
            })

        return context

    def get(self, request):
        group_id = request.GET.get("group_id")
        context = self.get_context_data(group_id)
        return render(request, self.template_name, context)

    def post(self, request):
        group_id = request.POST.get("group_id")
        group, members = get_group_with_members(int(group_id), request.user)

        for member in members:
            positive_data = member.positive_data.copy() if member.positive_data else {}
            negative_data = member.negative_data.copy() if member.negative_data else {}

            # Extract form data for this member
            for key, value in request.POST.items():
                if key.startswith(f"{member.id}_positive_"):
                    col_name = key.split("_positive_", 1)[1]
                    if col_name in positive_data:
                        positive_data[col_name] = value

                elif key.startswith(f"{member.id}_negative_"):
                    col_name = key.split("_negative_", 1)[1]
                    if col_name in negative_data:
                        negative_data[col_name] = value

            # Use service to update member data
            if "negative_save" in request.POST:
                MemberService.update_member_data(member, negative_data=negative_data)
            elif "positive_save" in request.POST:
                MemberService.update_member_data(member, positive_data=positive_data)

        context = self.get_context_data(group_id)
        return render(request, self.template_name, context)


class AddColumn(LoginRequiredMixin, TemplateView):
    template_name = "point_system/new_column.html"

    def get(self, request, pk):
        group = get_object_or_404(GroupCreationModel, id=pk, user=request.user)
        table_type = request.GET.get("table")
        return render(request, self.template_name, {
            "group_id": group.id,
            "table_type": table_type,
        })

    def post(self, request, pk):
        group = get_object_or_404(GroupCreationModel, id=pk, user=request.user)
        form = AddFieldForm(request.POST)

        if form.is_valid():
            field_name = form.cleaned_data["name"]
            field_type = form.cleaned_data["type"]
            field_definition = form.cleaned_data["field_definition"]

            try:
                if FieldDefinition.objects.filter(
                    group=group, name=field_name, definition=field_definition
                ).exists():
                    raise IntegrityError("Field already exists")

                FieldDefinition.objects.create(
                    group=group,
                    name=field_name,
                    type=field_type,
                    definition=field_definition,
                )

                # Use service to add field to all members
                MemberService.add_field_to_members(group, field_name, field_type, field_definition)

                return redirect(f"{reverse('karma:karma-home')}?group_id={group.id}")

            except IntegrityError:
                messages.error(
                    request,
                    f"A column named '{field_name}' already exists in {field_definition} table.",
                )
                return render(request, self.template_name, {
                    "group_id": group.id,
                    "table_type": field_definition,
                })

        return render(request, self.template_name, {"group_id": group.id})


class EditColumn(LoginRequiredMixin, TemplateView):
    template_name = "point_system/edit_column.html"

    def _get_field_keys(self, group, table_type):
        """Get field keys for the given table type."""
        fields = FieldDefinition.objects.filter(
            group=group, definition=table_type
        ).values_list("name", flat=True)
        return list(fields)

    def get(self, request, pk):
        group = get_object_or_404(GroupCreationModel, id=pk, user=request.user)
        table_type = request.GET.get("table")
        all_keys = self._get_field_keys(group, table_type)

        return render(request, self.template_name, {
            "group_id": group.id,
            "all_keys": all_keys,
            "table_type": table_type,
        })

    def post(self, request, pk):
        group = get_object_or_404(GroupCreationModel, id=pk, user=request.user)
        field_definition = request.POST.get("field_definition")
        form = EditColumnForm(request.POST)
        all_keys = self._get_field_keys(group, field_definition)

        if form.is_valid():
            new_name = form.cleaned_data["new_name"]
            old_name = form.cleaned_data["old_name"]

            try:
                # Use service to rename field
                MemberService.rename_field_for_members(group, old_name, new_name, field_definition)
                return redirect(f"{reverse('karma:karma-home')}?group_id={group.id}")

            except FieldDefinition.DoesNotExist:
                messages.error(request, f"Column '{old_name}' not found.")

            except IntegrityError:
                messages.error(request, f"A column named '{new_name}' already exists.")

        return render(request, self.template_name, {
            "group_id": group.id,
            "table_type": field_definition,
            "all_keys": all_keys,
        })


class DeleteColumn(LoginRequiredMixin, TemplateView):
    template_name = "point_system/delete_column.html"

    def _get_field_keys(self, group, table_type):
        """Get field keys for the given table type."""
        fields = FieldDefinition.objects.filter(
            group=group, definition=table_type
        ).values_list("name", flat=True)
        return list(fields)

    def get(self, request, pk):
        group = get_object_or_404(GroupCreationModel, id=pk, user=request.user)
        table_type = request.GET.get("table")
        all_keys = self._get_field_keys(group, table_type)

        return render(request, self.template_name, {
            "group_id": group.id,
            "all_keys": all_keys,
            "table_type": table_type,
        })

    def post(self, request, pk):
        group = get_object_or_404(GroupCreationModel, id=pk, user=request.user)
        field_definition = request.POST.get("field_definition")
        all_keys = self._get_field_keys(group, field_definition)

        form = RemoveFieldForm(request.POST, field_choices=sorted(all_keys))

        if form.is_valid():
            field_name = form.cleaned_data["field_name"]

            # Use service to remove field
            MemberService.remove_field_from_members(group, field_name, field_definition)

            return redirect(f"{reverse('karma:karma-home')}?group_id={group.id}")

        return render(request, self.template_name, {
            "group_id": group.id,
            "all_keys": all_keys,
            "table_type": field_definition,
        })


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "wip.html"

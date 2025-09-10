from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.group_maker.models import GroupCreationModel
from .forms import AddFieldForm, RemoveFieldForm, EditColumnForm
from django.views.generic import TemplateView
from django.db import IntegrityError
from django.contrib import messages
from .models import FieldDefinition
from django.urls import reverse


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "point_system/home.html"

    def get(self, request):
        group_id = request.GET.get("group_id")
        column_type_negative = {}
        column_type_positive = {}
        selected_group = None
        positive_column_names = []
        negative_column_names = []
        members = []

        if group_id:
            selected_group = get_object_or_404(
                GroupCreationModel, id=group_id, user=request.user
            )
            selected_group.sync_members()
            members = selected_group.karma_members.all()

            positive_columns = FieldDefinition.objects.filter(
                group=selected_group, definition="positive"
            ).order_by("created_at")
            negative_columns = FieldDefinition.objects.filter(
                group=selected_group, definition="negative"
            ).order_by("created_at")

            positive_column_names = [col.name for col in positive_columns]
            negative_column_names = [col.name for col in negative_columns]

            for col in positive_columns:
                column_type_positive[col.name] = (
                    "number" if col.type == "int" else "text"
                )
            for col in negative_columns:
                column_type_negative[col.name] = (
                    "number" if col.type == "int" else "text"
                )

            for member in members:
                member_positive_total = 0
                member_negative_total = 0

                if member.positive_data:
                    for _, value in member.positive_data.items():
                        try:
                            int_value = int(value)
                        except (ValueError, TypeError):
                            int_value = 0

                        if int_value:
                            member_positive_total += int_value
                    member.positive_total = member_positive_total

                if member.negative_data:
                    for _, value in member.negative_data.items():
                        try:
                            int_value = int(value)
                        except (ValueError, TypeError):
                            int_value = 0

                        if int_value:
                            member_negative_total += int_value
                    member.negative_total = member_negative_total

        return render(
            request,
            self.template_name,
            {
                "groups": GroupCreationModel.objects.filter(user=request.user),
                "selected_group": selected_group,
                "group_id": group_id,
                "members": members,
                "positive_data": positive_column_names,
                "negative_data": negative_column_names,
                "column_type_negative": column_type_negative,
                "column_type_positive": column_type_positive,
            },
        )

    def post(self, request):
        group_id = request.POST.get("group_id")
        selected_group = get_object_or_404(
            GroupCreationModel, id=group_id, user=request.user
        )
        selected_group.sync_members()
        members = selected_group.karma_members.all()
        column_type_negative = {}
        column_type_positive = {}

        for member in members:
            member_total_positive = 0
            member_total_negative = 0

            positive_data = member.positive_data.copy() if member.positive_data else {}
            negative_data = member.negative_data.copy() if member.negative_data else {}

            for key, value in request.POST.items():
                if key.startswith(f"{member.id}_positive_"):
                    col_name = key.split("_positive_", 1)[1]
                    if col_name in positive_data:
                        positive_data[col_name] = value

                elif key.startswith(f"{member.id}_negative_"):
                    col_name = key.split("_negative_", 1)[1]
                    if col_name in negative_data:
                        negative_data[col_name] = value

            if positive_data:
                for _, v in positive_data.items():
                    try:
                        int_value = int(v)
                    except (ValueError, TypeError):
                        int_value = 0
                    if int_value:
                        member_total_positive += int_value
                member.positive_total = member_total_positive
            else:
                member.positive_total = 0

            if negative_data:
                for _, v in negative_data.items():
                    try:
                        int_value = int(v)
                    except (ValueError, TypeError):
                        int_value = 0
                    if int_value:
                        member_total_negative += int_value
                member.negative_total = member_total_negative
            else:
                member.negative_total = 0

            if "negative_save" in request.POST:
                member.negative_data = negative_data

            elif "positive_save" in request.POST:
                member.positive_data = positive_data

            member.save()

        positive_columns = FieldDefinition.objects.filter(
            group=selected_group, definition="positive"
        ).order_by("created_at")
        negative_columns = FieldDefinition.objects.filter(
            group=selected_group, definition="negative"
        ).order_by("created_at")

        positive_column_names = [col.name for col in positive_columns]
        negative_column_names = [col.name for col in negative_columns]

        for col in positive_columns:
            column_type_positive[col.name] = "number" if col.type == "int" else "text"
        for col in negative_columns:
            column_type_negative[col.name] = "number" if col.type == "int" else "text"

        return render(
            request,
            self.template_name,
            {
                "groups": GroupCreationModel.objects.filter(user=request.user),
                "selected_group": selected_group,
                "group_id": group_id,
                "members": members,
                "positive_data": positive_column_names,
                "negative_data": negative_column_names,
                "column_type_negative": column_type_negative,
                "column_type_positive": column_type_positive,
            },
        )


class AddColumn(LoginRequiredMixin, TemplateView):
    template_name = "point_system/new_column.html"

    def get(self, request, pk):
        group = get_object_or_404(GroupCreationModel, id=pk, user=request.user)
        table_type = request.GET.get("table")
        context = {
            "group_id": group.id,
            "table_type": table_type,
        }

        return render(request, self.template_name, context)

    def post(self, request, pk):
        group = get_object_or_404(GroupCreationModel, id=pk, user=request.user)
        group.sync_members()
        members = group.karma_members.all()
        column_type = ""

        form = AddFieldForm(request.POST)

        if form.is_valid():
            field_name = request.POST.get("name")
            field_type = request.POST.get("type")
            field_definition = request.POST.get("field_definition")

            try:
                if FieldDefinition.objects.filter(
                    group=group, name=field_name, definition=field_definition
                ).exists():
                    raise IntegrityError()

                FieldDefinition.objects.create(
                    group=group,
                    name=field_name,
                    type=field_type,
                    definition=field_definition,
                )

            except IntegrityError as e:
                print(f"IntegrityError details: {e}")

                messages.error(
                    request,
                    f"A column named '{field_name}' already exists in {field_definition} table.",
                )
                return render(
                    request,
                    self.template_name,
                    {
                        "group_id": group.id,
                        "add_field_form": AddFieldForm(),
                        "table_type": field_definition,
                        "column_type": column_type,
                    },
                )

            if field_type == "int":
                default = 0
                column_type = "number"
            else:
                default = ""
                column_type = "text"

            for member in members:
                if field_definition == "positive":
                    if member.positive_data is None:
                        member.positive_data = {}

                    if field_name not in member.positive_data:
                        member.positive_data[field_name] = default

                elif field_definition == "negative":
                    if member.negative_data is None:
                        member.negative_data = {}

                    if field_name not in member.negative_data:
                        member.negative_data[field_name] = default

                member.save()

            return redirect(f"{reverse('karma:karma-home')}?group_id={group.id}")

        return render(
            request,
            self.template_name,
            {
                "group_id": group.id,
            },
        )


class EditColumn(LoginRequiredMixin, TemplateView):
    template_name = "point_system/edit_column.html"

    def get(self, request, pk):
        group = get_object_or_404(GroupCreationModel, id=pk, user=request.user)
        members = group.karma_members.all()
        table_type = request.GET.get("table")
        all_keys = []

        for member in members:
            if table_type == "negative":
                all_keys = [
                    key for key in member.negative_data.keys() if member.negative_data
                ]

            elif table_type == "positive":
                all_keys = [
                    key for key in member.positive_data.keys() if member.positive_data
                ]

        context = {
            "group_id": group.id,
            "all_keys": all_keys,
            "table_type": table_type,
        }

        return render(request, self.template_name, context)

    def post(self, request, pk):
        group = get_object_or_404(GroupCreationModel, id=pk, user=request.user)
        field_definition = request.POST.get("field_definition")
        members = group.karma_members.all()
        form = EditColumnForm(request.POST)
        group.sync_members()
        member = members[0]

        if field_definition == "negative" and member.negative_data:
            all_keys = list(member.negative_data.keys())

        elif field_definition == "positive" and member.positive_data:
            all_keys = list(member.positive_data.keys())

        if form.is_valid():
            new_name = form.cleaned_data["new_name"]
            old_name = form.cleaned_data["old_name"]

            try:
                column = FieldDefinition.objects.get(
                    group=group, name=old_name, definition=field_definition
                )
                column.name = new_name
                column.save()

                for member in members:
                    if field_definition == "positive":
                        if member.positive_data and old_name in member.positive_data:
                            member.positive_data[new_name] = member.positive_data.pop(
                                old_name
                            )

                    elif field_definition == "negative":
                        if member.negative_data and old_name in member.negative_data:
                            member.negative_data[new_name] = member.negative_data.pop(
                                old_name
                            )

                    member.save()

            except FieldDefinition.DoesNotExist:
                messages.error(request, f"Column '{old_name}' not found.")

            except IntegrityError:
                messages.error(request, f"A column named '{new_name}' already exists.")

                return render(
                    request,
                    self.template_name,
                    {
                        "group_id": group.id,
                        "table_type": field_definition,
                        "all_keys": all_keys,
                    },
                )

            return redirect(f"{reverse('karma:karma-home')}?group_id={group.id}")

        return render(
            request,
            self.template_name,
            {
                "table_type": field_definition,
                "group_id": group.id,
                "all_keys": all_keys,
            },
        )


class DeleteColumn(LoginRequiredMixin, TemplateView):
    template_name = "point_system/delete_column.html"

    def get(self, request, pk):
        group = get_object_or_404(GroupCreationModel, id=pk, user=request.user)
        members = group.karma_members.all()
        field_definition = request.GET.get("table")

        member = members[0]
        if field_definition == "negative":
            all_keys = [
                key for key in member.negative_data.keys() if member.negative_data
            ]
        elif field_definition == "positive":
            all_keys = [
                key for key in member.positive_data.keys() if member.positive_data
            ]

        context = {
            "group_id": group.id,
            "all_keys": all_keys,
            "table_type": field_definition,
        }

        return render(request, self.template_name, context)

    def post(self, request, pk):
        group = get_object_or_404(GroupCreationModel, id=pk, user=request.user)
        field_definition = request.POST.get("field_definition")
        members = group.karma_members.all()
        group.sync_members()
        member = members[0]

        if field_definition == "negative" and member.negative_data:
            all_keys = list(member.negative_data.keys())

        elif field_definition == "positive" and member.positive_data:
            all_keys = list(member.positive_data.keys())

        form = RemoveFieldForm(request.POST, field_choices=sorted(all_keys))

        if form.is_valid():
            field_name = form.cleaned_data["field_name"]

            for member in members:
                if field_definition == "positive":
                    if field_name in member.positive_data:
                        del member.positive_data[field_name]

                elif field_definition == "negative":
                    if field_name in member.negative_data:
                        del member.negative_data[field_name]

                member.save()

            field = FieldDefinition.objects.filter(
                group=group, name=field_name, definition=field_definition
            ).first()

            if field:
                field.delete()

            return redirect(f"{reverse('karma:karma-home')}?group_id={group.id}")

        return render(
            request,
            self.template_name,
            {
                "group_id": group.id,
                "all_keys": all_keys,
                "table_type": field_definition,
            },
        )


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "wip.html"

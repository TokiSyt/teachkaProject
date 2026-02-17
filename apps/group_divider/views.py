from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.views.generic import TemplateView

from apps.group_maker.models import GroupCreationModel
from apps.users.models import UserStats

from .forms import GroupMakerForm
from .services.group_split import get_split_group_color
from .services.group_split import group_split as group_split_f


class GroupDividerHome(LoginRequiredMixin, TemplateView):
    template_name = "group_divider/home.html"
    form_class = GroupMakerForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["groups"] = GroupCreationModel.objects.filter(user=self.request.user)
        context["form"] = self.form_class()
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            selected_group_id = form.cleaned_data["group_id"]
            selected_group_size = form.cleaned_data["size"]
            selected_group = get_object_or_404(GroupCreationModel, id=selected_group_id, user=request.user)
            members = list(selected_group.get_members())
            raw_splitted_group = group_split_f(members, selected_group_size)
            groups = GroupCreationModel.objects.filter(user=self.request.user)

            stats, _ = UserStats.objects.get_or_create(user=request.user)
            stats.divider_uses += 1
            stats.save(update_fields=["divider_uses"])
            colored_splitted_groups = get_split_group_color(raw_splitted_group)
            return render(
                request,
                "group_divider/home.html",
                {
                    "form": form,
                    "splitted_group": colored_splitted_groups,
                    "selected_group": selected_group,
                    "groups": groups,
                },
            )
        groups = GroupCreationModel.objects.filter(user=request.user)
        return render(request, "group_divider/home.html", {"form": form, "groups": groups})

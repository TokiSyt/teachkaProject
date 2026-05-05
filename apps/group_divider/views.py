from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import TemplateView

from apps.group_maker.models import GroupCreationModel
from apps.users.models import UserStats

from .forms import GroupMakerForm
from .services.group_split import get_split_group_color
from .services.group_split import group_split as group_split_f

SESSION_RESULT_KEY = "group_divider_result"


def _serialize_split(splitted_teams):
    """Convert split result (Member instances + color) to JSON-safe form for session."""
    out = []
    for team in splitted_teams:
        *members, color = team
        out.append([{"name": m.name} for m in members] + [color])
    return out


class GroupDividerHome(LoginRequiredMixin, TemplateView):
    template_name = "group_divider/home.html"
    form_class = GroupMakerForm

    def get(self, request, *args, **kwargs):
        if request.GET.get("reset"):
            request.session.pop(SESSION_RESULT_KEY, None)
            return redirect(reverse("group_divider:home"))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["groups"] = GroupCreationModel.objects.filter(user=self.request.user)

        result = self.request.session.get(SESSION_RESULT_KEY, None)
        initial = {}
        if result and result.get("splitted_teams") and result.get("selected_group_id"):
            selected_group = GroupCreationModel.objects.filter(
                id=result["selected_group_id"], user=self.request.user
            ).first()
            if selected_group:
                context["splitted_teams"] = result["splitted_teams"]
                context["selected_group"] = selected_group
                initial = {"group_id": result["selected_group_id"], "size": result.get("size")}

        context["form"] = self.form_class(initial=initial)
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if not form.is_valid():
            groups = GroupCreationModel.objects.filter(user=request.user)
            return render(request, self.template_name, {"form": form, "groups": groups})

        selected_group_id = form.cleaned_data["group_id"]
        selected_group_size = form.cleaned_data["size"]
        selected_group = get_object_or_404(GroupCreationModel, id=selected_group_id, user=request.user)
        members = list(selected_group.get_members())
        raw_splitted_teams = group_split_f(members, selected_group_size)
        colored_splitted_teams = get_split_group_color(raw_splitted_teams)

        stats, _ = UserStats.objects.get_or_create(user=request.user)
        stats.divider_uses += 1
        stats.save(update_fields=["divider_uses"])

        request.session[SESSION_RESULT_KEY] = {
            "splitted_teams": _serialize_split(colored_splitted_teams),
            "selected_group_id": selected_group_id,
            "size": selected_group_size,
        }
        return redirect(reverse("group_divider:home"))

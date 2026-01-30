from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.views.generic import TemplateView

from apps.core.models import Member
from apps.group_maker.models import GroupCreationModel

from .services.utils import choose_random_member


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "wheel/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["groups"] = GroupCreationModel.objects.filter(user=self.request.user)
        return context

    def get(self, request, *args, **kwargs):
        selected_group = None

        if "reset" in request.GET:
            for key in list(request.session.keys()):
                if key.startswith("already_chosen_members_"):
                    request.session.pop(key, None)
                request.session.modified = True

        selected_group_id = request.GET.get("group_id")
        if selected_group_id:
            selected_group = get_object_or_404(GroupCreationModel, id=selected_group_id, user=request.user)

        context = self.get_context_data(**kwargs)
        if selected_group:
            context["selected_group"] = selected_group
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        groups = GroupCreationModel.objects.filter(user=self.request.user)
        selected_group_id = request.POST.get("group_id")  # tag: select, field: name="group_id"

        if selected_group_id:
            selected_group = get_object_or_404(GroupCreationModel, id=selected_group_id, user=request.user)
            members = selected_group.get_members()
            member_count = members.count()

            session_key = f"already_chosen_members_{selected_group.id}"
            already_chosen_ids = request.session.get(session_key, [])

            if len(already_chosen_ids) >= member_count:
                already_chosen_members = Member.objects.filter(id__in=already_chosen_ids)
                return render(
                    request,
                    self.template_name,
                    {
                        "chosen_member": None,
                        "already_chosen_members": already_chosen_members,
                        "selected_group": selected_group,
                        "groups": groups,
                        "message": "All members chosen! Click Reset to start over.",
                    },
                )

            chosen_member, already_chosen_ids = choose_random_member(members, already_chosen_ids)

            # Handle case where all members have been chosen
            if chosen_member is None:
                already_chosen_members = Member.objects.filter(id__in=already_chosen_ids)
                return render(
                    request,
                    self.template_name,
                    {
                        "chosen_member": None,
                        "already_chosen_members": already_chosen_members,
                        "selected_group": selected_group,
                        "groups": groups,
                        "message": "All members chosen! Click Reset to start over.",
                    },
                )

            request.session[session_key] = already_chosen_ids
            request.session.modified = True

            # Track usage
            request.user.wheel_spins += 1
            request.user.save(update_fields=["wheel_spins"])

            already_chosen_members = Member.objects.filter(id__in=already_chosen_ids)
            return render(
                request,
                self.template_name,
                {
                    "chosen_member": chosen_member,
                    "already_chosen_members": already_chosen_members,
                    "selected_group": selected_group,
                    "groups": groups,
                },
            )

        return render(request, "wheel/home.html")

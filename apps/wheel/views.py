from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import TemplateView

from apps.core.models import Member
from apps.group_maker.models import GroupCreationModel

from .forms import NameWheelForm
from .services.utils import choose_random_member


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "wheel/home.html"
    form_class = NameWheelForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["groups"] = GroupCreationModel.objects.filter(user=self.request.user).prefetch_related("members")
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

        # Check for message from POST redirect
        message = request.session.pop("wheel_message", None)
        if message:
            context["message"] = message
            request.session.modified = True

        if selected_group:
            context["selected_group"] = selected_group

            # Check for spin results from POST redirect
            spin_result_key = f"spin_result_{selected_group.id}"
            spin_result = request.session.pop(spin_result_key, None)
            if spin_result:
                chosen_member_ids = spin_result.get("chosen_member_ids", [])
                context["chosen_members"] = Member.objects.filter(id__in=chosen_member_ids)
                context["members_chosen"] = spin_result.get("members_chosen", 1)
                request.session.modified = True

            # Get already chosen members
            session_key = f"already_chosen_members_{selected_group.id}"
            already_chosen_ids = request.session.get(session_key, [])
            if already_chosen_ids:
                context["already_chosen_members"] = Member.objects.filter(id__in=already_chosen_ids)

        return self.render_to_response(context)

    def _is_ajax(self, request):
        return request.headers.get("X-Requested-With") == "XMLHttpRequest"

    def post(self, request, *args, **kwargs):
        is_ajax = self._is_ajax(request)
        selected_group_id = request.POST.get("group_id")

        if not selected_group_id:
            if is_ajax:
                return JsonResponse({"error": "No group selected"}, status=400)
            context = self.get_context_data()
            context["message"] = "Please select a group first."
            return render(request, self.template_name, context)

        selected_group = get_object_or_404(GroupCreationModel, id=selected_group_id, user=request.user)
        members = selected_group.get_members()
        member_count = members.count()

        session_key = f"already_chosen_members_{selected_group.id}"

        if request.POST.get("clear_session") == "1":
            request.session.pop(session_key, None)
            request.session.modified = True

        already_chosen_ids = request.session.get(session_key, [])
        remove_after_spin = request.POST.get("remove_after_spin") == "on"

        if remove_after_spin and len(already_chosen_ids) >= member_count:
            if is_ajax:
                return JsonResponse(
                    {
                        "error": "All members chosen! Click Reset to start over.",
                        "all_chosen": True,
                    }
                )
            request.session["wheel_message"] = "All members chosen! Click Reset to start over."
            request.session.modified = True
            return redirect(f"{reverse('wheel:home')}?group_id={selected_group.id}")

        # Reset already_chosen_ids if not removing after spin
        if not remove_after_spin:
            already_chosen_ids = []

        chosen_members = []
        members_chosen_amount = int(request.POST.get("members_chosen", 1))
        for _ in range(members_chosen_amount):
            chosen_member, already_chosen_ids = choose_random_member(members, already_chosen_ids)
            if chosen_member:
                chosen_members.append(chosen_member)

        if not chosen_members:
            if is_ajax:
                return JsonResponse(
                    {
                        "error": "All members chosen! Click Reset to start over.",
                        "all_chosen": True,
                    }
                )
            request.session["wheel_message"] = "All members chosen! Click Reset to start over."
            request.session.modified = True
            return redirect(f"{reverse('wheel:home')}?group_id={selected_group.id}")

        # Update session only if removing after spin
        if remove_after_spin:
            request.session[session_key] = already_chosen_ids
            request.session.modified = True

        # Track usage
        request.user.wheel_spins += 1
        request.user.save(update_fields=["wheel_spins"])

        if is_ajax:
            return JsonResponse(
                {
                    "chosen_members": [m.name for m in chosen_members],
                    "chosen_ids": [m.id for m in chosen_members],
                    "already_chosen_ids": already_chosen_ids,
                }
            )

        # Non-AJAX: store in session and redirect
        spin_result_key = f"spin_result_{selected_group.id}"
        request.session[spin_result_key] = {
            "chosen_member_ids": [m.id for m in chosen_members],
            "members_chosen": members_chosen_amount,
        }
        request.session.modified = True
        return redirect(f"{reverse('wheel:home')}?group_id={selected_group.id}")

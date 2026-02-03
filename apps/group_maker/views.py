from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView

from .forms import GroupCreationForm
from .models import GroupCreationModel


class GroupHome(LoginRequiredMixin, TemplateView):
    template_name = "group_maker/home.html"
    form_class = GroupCreationForm
    model = GroupCreationModel

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["groups"] = GroupCreationModel.objects.filter(user=self.request.user)
        context["form"] = self.form_class()
        return context


class GroupCreate(LoginRequiredMixin, CreateView):
    model = GroupCreationModel
    template_name = "group_maker/list_create.html"
    form_class = GroupCreationForm

    def form_valid(self, form):
        form.instance.user = self.request.user
        # Note: sync_members is handled automatically by post_save signal
        return super().form_valid(form)

    def get_success_url(self):
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={self.request.get_host()}):
            return next_url
        return "/"


class GroupUpdate(LoginRequiredMixin, UpdateView):
    model = GroupCreationModel
    template_name = "group_maker/list_edit.html"
    form_class = GroupCreationForm

    def get_success_url(self):
        origin_app = self.request.POST.get("origin_app") or self.request.GET.get("origin_app")
        if origin_app and origin_app.strip():
            return reverse(f"{origin_app}:home")
        return reverse("home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_group"] = self.object
        context["members"] = self.object.members.all()
        origin_app = self.request.GET.get("origin_app")
        context["origin_app"] = origin_app
        if origin_app and origin_app.strip():
            context["cancel_url"] = reverse(f"{origin_app}:home")
        else:
            context["cancel_url"] = self.request.META.get("HTTP_REFERER") or reverse("home")
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        for member in self.object.members.all():
            color_key = f"member_color_{member.id}"
            if color_key in self.request.POST:
                new_color = self.request.POST[color_key]
                if new_color and new_color != member.color:
                    member.color = new_color
                    member.save(update_fields=["color"])
        return response


class GroupDelete(LoginRequiredMixin, DeleteView):  # type: ignore[misc]
    model = GroupCreationModel
    template_name = "group_maker/confirm_delete.html"

    def get_success_url(self):
        origin_app = self.request.POST.get("origin_app") or self.request.GET.get("origin_app")
        if origin_app and origin_app.strip():
            return reverse(f"{origin_app}:home")
        return reverse("home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_group"] = self.object
        origin_app = self.request.GET.get("origin_app")
        context["origin_app"] = origin_app
        if origin_app and origin_app.strip():
            # Came from edit page, cancel goes back to edit
            edit_url = reverse("group_maker:group-maker-edit", args=[self.object.id])
            context["cancel_url"] = f"{edit_url}?origin_app={origin_app}"
        else:
            # Direct access, cancel goes to referer or home
            context["cancel_url"] = self.request.META.get("HTTP_REFERER") or reverse("home")
        return context

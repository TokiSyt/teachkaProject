from django.views.generic import FormView, TemplateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.urls import reverse_lazy
from .forms import RegisterForm, EditProfileForm, CustomPasswordChangeForm
from django.contrib.auth import get_user_model


User = get_user_model()


class RegisterView(FormView):
    template_name = "registration/register.html"
    form_class = RegisterForm
    success_url = reverse_lazy("home")

    def form_valid(self, form):

        new_user = form.save()
        new_user = authenticate(
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password1"],
        )

        login(self.request, new_user)

        context = self.get_context_data(form=form)
        return super().form_valid(context)

    def form_invalid(self, form):
        return super().form_invalid(form)


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "users/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_data"] = self.request.user
        return context


class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = "wip.html"


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = EditProfileForm
    template_name = "users/edit_profile.html"
    success_url = reverse_lazy("profile")

    def get_object(self, queryset=None):
        return self.request.user


class ChangePassword(LoginRequiredMixin, FormView):
    form_class = CustomPasswordChangeForm
    template_name = "users/change_password.html"
    success_url = reverse_lazy("profile")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, form.user)
        return super().form_valid(form)

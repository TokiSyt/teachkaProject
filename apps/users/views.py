from django.contrib import messages
from django.contrib.auth import (
    get_user_model,
    login,
    update_session_auth_hash,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View
from django.views.generic import FormView, TemplateView, UpdateView

from teachkaBaseProject.tokens import account_activation_token

from .forms import CustomPasswordChangeForm, EditProfileForm, RegisterForm

User = get_user_model()


class RegisterView(FormView):
    template_name = "registration/register.html"
    form_class = RegisterForm
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        new_user = form.save(commit=False)
        new_user.is_active = False
        new_user.save()

        current_site = get_current_site(self.request)
        mail_subject = "Welcome to Teachka!"
        message = render_to_string(
            "registration/account_activation_email.html",
            {
                "user": new_user,
                "domain": current_site.domain,
                "uid": urlsafe_base64_encode(force_bytes(new_user.pk)),
                "token": account_activation_token.make_token(new_user),
            },
        )
        to_email = form.cleaned_data.get("email")
        email = EmailMessage(mail_subject, message, to=[to_email])
        email.send()
        messages.success(self.request, "Welcome, please check your email to complete your registration.")
        return redirect("home")

    def form_invalid(self, form):
        return super().form_invalid(form)


class ActivateAccountView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            login(request, user)
            messages.success(request, "Your account has been successfully activated!")
            return redirect(reverse("home"))
        else:
            messages.error(request, "Activation link is invalid or expired.")
            return redirect("home")


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "users/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_data"] = self.request.user
        return context


class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = "users/settings.html"

    def post(self, request):
        profile = request.user
        updated = False

        if "icon_hover_color" in request.POST:
            profile.icon_hover_color = request.POST["icon_hover_color"]
            updated = True

        if "theme" in request.POST:
            profile.theme = request.POST["theme"]
            updated = True

        if "toggle_theme" in request.POST:
            theme_cycle = {"light": "dark", "dark": "pastel", "pastel": "light"}
            profile.theme = theme_cycle.get(profile.theme, "light")
            updated = True

        if updated:
            profile.save()

        return redirect(request.path)


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


class ThemeUpdateView(LoginRequiredMixin, View):
    """AJAX endpoint for updating user theme."""

    def post(self, request):
        theme = request.POST.get("theme")
        if theme in ["light", "dark", "pastel"]:
            request.user.theme = theme
            request.user.save(update_fields=["theme"])
            return JsonResponse({"status": "ok", "theme": theme})
        return JsonResponse({"status": "error", "message": "Invalid theme"}, status=400)

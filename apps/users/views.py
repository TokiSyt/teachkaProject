import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    get_user_model,
    login,
    logout,
)
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View
from django.views.generic import FormView, TemplateView, UpdateView

from teachkaBaseProject.tokens import account_activation_token

from .forms import EditProfileForm, PasswordResetRequestForm, RegisterForm

User = get_user_model()
password_reset_token = PasswordResetTokenGenerator()


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
        messages.success(
            self.request,
            "Welcome, please check your email to complete your registration.",
        )
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
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
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
            color = request.POST["icon_hover_color"]
            if re.fullmatch(r"#[0-9a-fA-F]{3,6}", color):
                profile.icon_hover_color = color
                updated = True

        if "language" in request.POST:
            lang = request.POST["language"]
            if lang in ["en", "pt", "cs"]:
                profile.language = lang
                updated = True

        if updated:
            profile.save()

        return redirect(request.path)


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = EditProfileForm
    template_name = "users/edit_profile.html"
    success_url = reverse_lazy("profile:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        email = form.cleaned_data.get("email")
        if User.objects.exclude(pk=self.request.user.pk).filter(email=email).exists():
            form.add_error("email", "An account with this email address already exists.")
            return self.form_invalid(form)
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)


class ChangePassword(LoginRequiredMixin, FormView):
    form_class = PasswordResetRequestForm
    template_name = "users/change_password.html"
    success_url = reverse_lazy("profile:edit_profile")

    def form_valid(self, form):
        to_email = form.cleaned_data.get("send_to_email")
        if User.objects.filter(email=to_email, pk=self.request.user.pk).exists():
            current_site = get_current_site(self.request)
            mail_subject = "You have requested a new password"
            message = render_to_string(
                "users/password_reset_email.html",
                {
                    "user": self.request.user,
                    "domain": current_site.domain,
                    "uid": urlsafe_base64_encode(force_bytes(self.request.user.pk)),
                    "token": password_reset_token.make_token(self.request.user),
                },
            )
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.send()
        messages.success(
            self.request,
            "You will receive a password reset link in the email registered",
        )
        return redirect("home")

    def form_invalid(self, form):
        return super().form_invalid(form)


class PasswordResetView(View):
    def _get_user_from_token(self, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None
        if password_reset_token.check_token(user, token):
            return user
        return None

    def get(self, request, uidb64, token):
        user = self._get_user_from_token(uidb64, token)

        if user is not None:
            form = SetPasswordForm(user)
            return render(request, "users/password_reset.html", {"form": form, "uidb64": uidb64, "token": token})

        messages.error(request, "Reset link is invalid or expired.")
        return redirect("home")

    def post(self, request, uidb64, token):
        user = self._get_user_from_token(uidb64, token)
        if user is None:
            messages.error(request, "Reset link is invalid or expired.")
            return redirect("home")

        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            logout(request)
            messages.success(request, "Your password was successfully reset. You may now login again.")
            return redirect("home")

        return render(request, "users/password_reset.html", {"form": form, "uidb64": uidb64, "token": token})


class ThemeUpdateView(LoginRequiredMixin, View):
    """AJAX endpoint for updating user theme."""

    def post(self, request):
        theme = request.POST.get("theme")
        if theme in ["light", "dark", "pastel"]:
            request.user.theme = theme
            request.user.save(update_fields=["theme"])
            return JsonResponse({"status": "ok", "theme": theme})
        return JsonResponse({"status": "error", "message": "Invalid theme"}, status=400)


class LanguageUpdateView(View):
    """AJAX endpoint for updating user language."""

    def post(self, request):
        lang = request.POST.get("language")
        if lang not in ["en", "pt", "cs"]:
            return JsonResponse({"status": "error", "message": "Invalid language"}, status=400)

        if request.user.is_authenticated:
            request.user.language = lang
            request.user.save(update_fields=["language"])

        response = JsonResponse({"status": "ok", "language": lang})
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            lang,
            max_age=365 * 24 * 60 * 60,
            path=settings.LANGUAGE_COOKIE_PATH,
            domain=settings.LANGUAGE_COOKIE_DOMAIN,
            secure=settings.LANGUAGE_COOKIE_SECURE,
            httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
            samesite=settings.LANGUAGE_COOKIE_SAMESITE,
        )
        return response

from django.urls import path

from .views import (
    ActivateAccountView,
    ChangePassword,
    EditProfileView,
    PasswordResetView,
    ProfileView,
    SettingsView,
    ThemeUpdateView,
)

app_name = "profile"

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/edit/", EditProfileView.as_view(), name="edit_profile"),
    path("profile/password/", ChangePassword.as_view(), name="change-password"),
    path("reset/password/<str:uidb64>/<str:token>/", PasswordResetView.as_view(), name="password-reset"),
    path("settings/", SettingsView.as_view(), name="settings"),
    path("theme/", ThemeUpdateView.as_view(), name="theme-update"),
    path("activate/<str:uidb64>/<str:token>/", ActivateAccountView.as_view(), name="activate"),
]

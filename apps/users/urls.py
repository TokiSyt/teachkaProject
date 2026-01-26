from django.urls import path

from .views import ChangePassword, EditProfileView, ProfileView, SettingsView

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/edit/", EditProfileView.as_view(), name="edit_profile"),
    path("profile/password/", ChangePassword.as_view(), name="change-password"),
    path("settings/", SettingsView.as_view(), name="settings"),
]

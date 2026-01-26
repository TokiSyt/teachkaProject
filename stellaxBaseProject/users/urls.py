from django.urls import path
from . import views

urlpatterns = [
    path("profile/", views.profile_view, name="profile"),
    path("settings/", views.user_settings, name="settings"),
]

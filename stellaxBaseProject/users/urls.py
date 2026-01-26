from django.urls import path
from . import views

urlpatterns = [path("profile/", views.profileView, name="profile"), path("settings/", views.userSettings, name="settings")]

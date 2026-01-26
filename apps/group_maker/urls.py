from django.urls import path

from .views import (
    GroupCreate,
    GroupDelete,
    GroupHome,
    GroupUpdate,
)

app_name = "group_maker"

urlpatterns = [
    path("", GroupHome.as_view(), name="group-maker-home"),
    path("group_maker_creation/", GroupCreate.as_view(), name="group-maker-creation"),
    path("group_maker_edit/<int:pk>", GroupUpdate.as_view(), name="group-maker-edit"),
    path("group_maker_delete/<int:pk>", GroupDelete.as_view(), name="group-maker-delete"),
]

from django.urls import path
from .views import (
    GroupMakerHome,
    GroupMakerListCreate,
    GroupMakerListUpdate,
    GroupMakerListDelete,
)

urlpatterns = [
    path("", GroupMakerHome.as_view(), name="list-home"),
    path("list-creation/", GroupMakerListCreate.as_view(), name="list-creation"),
    path("list-edit/<int:pk>", GroupMakerListUpdate.as_view(), name="list-edit"),
    path("list-delete/<int:pk>", GroupMakerListDelete.as_view(), name="list-delete"),
]
